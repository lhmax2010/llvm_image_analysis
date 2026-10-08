/*
 * libthor - Tizen Thor communication protocol
 *
 * Licensed under the Apache License, Version 2.0 (the License);
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <assert.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>

#include "thor.h"
#include "thor_internal.h"
#include "thor_transport.h"

thor_device_handle *thor_init(enum thor_transport_type type)
{
	thor_device_handle *th;
	int ret;

	th = calloc(1, sizeof(*th));
	if (!th)
		return NULL;

	th->type = type;

	ret = t_thor_init(th);
	if (ret < 0) {
		free(th);
		th = NULL;
	}

	return th;
}

void thor_cleanup(thor_device_handle *th)
{
	if (!th)
		return;

	t_thor_cleanup(th);
	free(th);
}

static int thor_do_handshake(thor_device_handle *th)
{
	char challenge[] = "THOR";
	char response[] = "ROHT";
	char buffer[sizeof(response)];
	int ret;

	ret = t_thor_send(th, (unsigned char *)challenge, sizeof(challenge) - 1,
			  DEFAULT_TIMEOUT);
	if (ret < 0)
		return ret;

	ret = t_thor_recv(th, (unsigned char *)buffer, sizeof(buffer) - 1,
			  DEFAULT_TIMEOUT);
	if (ret < 0)
		return ret;

	buffer[sizeof(buffer) - 1] = '\0';

	if (strcmp(buffer, response))
		return -EINVAL;

	return 0;
}

int thor_open(thor_device_handle *th, struct thor_device_id *dev_id, int wait)
{
	int ret;

	if (!th)
		return -ENOENT;

	ret = t_thor_open(th, dev_id, wait);
	if (ret)
		return ret;

	ret = thor_do_handshake(th);
	if (ret) {
		thor_close(th);
		return ret;
	}

	return 0;
}

void thor_close(thor_device_handle *th)
{
	if (!th)
		return;

	t_thor_close(th);
}

static int thor_send_req(thor_device_handle *th, request_type req_id,
			 int req_sub_id, int *idata, int icnt,
			 char **sdata, int scnt)
{
	struct rqt_pkt req;
	int i;
	int ret;

	assert(icnt <= ARRAY_SIZE(req.int_data));
	assert(icnt >= 0);
	assert(scnt <= ARRAY_SIZE(req.str_data));
	assert(scnt >= 0);

	memset(&req, 0, sizeof(req));

	req.id = req_id;
	req.sub_id = req_sub_id;

	if (idata) {
		for (i = 0; i < icnt; i++)
			req.int_data[i] = idata[i];
	}

	if (sdata) {
		for (i = 0; i < scnt; i++)
			strncpy(req.str_data[i], sdata[i], 32);
	}

	ret = t_thor_send(th, (unsigned char *)&req, RQT_PKT_SIZE,
			  DEFAULT_TIMEOUT);

	return ret;
}

static inline int thor_recv_req(thor_device_handle *th, struct res_pkt *resp)
{
	return t_thor_recv(th, (unsigned char *)resp, sizeof(*resp),
			   DEFAULT_TIMEOUT);
}

static int thor_exec_cmd_full(thor_device_handle *th,  request_type req_id,
			      int req_sub_id, int *idata, int icnt,
			      char **sdata, int scnt, struct res_pkt *res)
{
	int ret;
	struct res_pkt resp;

	if (!res)
		res = &resp;

	ret = thor_send_req(th, req_id, req_sub_id, idata, icnt,
			    sdata, scnt);
	if (ret < 0)
		return ret;

	ret = thor_recv_req(th, res);
	if (ret < 0)
		return ret;

	return res->ack;
}

static inline int thor_exec_cmd(thor_device_handle *th,  request_type req_id,
				int req_sub_id, int *idata, int icnt)
{
	return thor_exec_cmd_full(th, req_id, req_sub_id, idata, icnt,
				  NULL, 0, NULL);
}

int thor_get_proto_ver(thor_device_handle *th)
{
	int ret;
	struct res_pkt resp;

	if (!th)
		return -ENOENT;

	ret = thor_exec_cmd_full(th, RQT_INFO, RQT_INFO_VER_PROTOCOL,
				 NULL, 0, NULL, 0, &resp);
	if (!ret)
		ret = (resp.int_data[0] << 8) | resp.int_data[1];

	return ret;
}

int thor_start_session(thor_device_handle *th, off_t total)
{
	int ret;
	uint32_t int_data[2];

	int_data[0] = (uint32_t)(total & 0xffffffff);
	int_data[1] = (uint32_t)((total >> 32) & 0xffffffff);

	ret = thor_exec_cmd(th, RQT_DL, RQT_DL_INIT, int_data,
			    ARRAY_SIZE(int_data));

	return ret;
}

int thor_end_session(thor_device_handle *th)
{
	int ret;

	if (!th)
		return -ENOENT;

	return thor_exec_cmd(th, RQT_DL, RQT_DL_EXIT, NULL, 0);
}

int thor_send_data(thor_device_handle *th, struct thor_data_src *data,
		   enum thor_data_type type, thor_progress_cb report_progress,
		   void *user_data, thor_next_entry_cb report_next_entry,
		   void *ne_cb_data)
{
	off_t filesize;
	const char *filename;
	const char *str_data[2] = { NULL, NULL };
	int scnt;
	struct res_pkt resp;
	int32_t int_data[3];
	off_t trans_unit_size;
	int ret;

	while (1) {
		ret = data->next_file(data);
		if (ret <= 0)
			break;
		if (report_next_entry)
			report_next_entry(th, data, ne_cb_data);

		filesize = data->get_file_length(data);
		filename = data->get_name(data);

		int_data[0] = type;
		int_data[1] = (uint32_t)(filesize & 0xffffffff);
		int_data[2] = (uint32_t)((filesize >> 32) & 0xffffffff);

		if (strlen(filename) <= 32) {
			/*
			 * THOR protocol only allows file name at most 32 with
			 * [RQT_DL, RQT_DL_FILE_INFO] request in
			 * rqt_pkt.str_data[0].
			 */
			scnt = 1;
			str_data[0] = filename;
		} else {
			/*
			 * Exceptionally, ARTIK boards require 33 lenght dtb
			 * file name from artik u-boot by misusing wrong lthor
			 * rqt_pkt.str_data usage, so append additional string
			 * to rqt_pkt.str_data[1].
			 */
			scnt = 2;
			str_data[0] = filename;
			str_data[1] = filename + 32;
		}

		if (!th)
			continue;

		ret = thor_exec_cmd_full(th, RQT_DL, RQT_DL_FILE_INFO,
					 int_data, ARRAY_SIZE(int_data),
					 (char **)str_data, scnt, &resp);
		if (ret < 0)
			return ret;

		trans_unit_size = resp.int_data[0];

		ret = thor_exec_cmd(th, RQT_DL, RQT_DL_FILE_START,
				    NULL, 0);
		if (ret < 0)
			return ret;

		ret = t_thor_send_raw_data(th, data, trans_unit_size,
					   report_progress, user_data);
		if (ret < 0)
			return ret;

		if (th) {
			ret = thor_exec_cmd(th, RQT_DL, RQT_DL_FILE_END,
					    NULL, 0);
			if (ret < 0)
				return ret;
		}
	}

	return 0;
}

int thor_reboot(thor_device_handle *th)
{
	if (!th)
		return -ENOENT;

	return thor_exec_cmd(th, RQT_CMD, RQT_CMD_REBOOT, NULL, 0);
}

int thor_get_data_src(const char *path, enum thor_data_src_format format,
		      struct thor_data_src **data)
{
	int ret;

	switch (format) {
	case THOR_FORMAT_RAW:
		ret = t_file_get_data_src(path, data);
		break;
	case THOR_FORMAT_TAR:
		ret = t_tar_get_data_src(path, data);
		break;
	default:
		ret = -ENOTSUP;
	}

	return ret;
}

void thor_release_data_src(struct thor_data_src *data)
{
	if (data->release)
		data->release(data);
}
