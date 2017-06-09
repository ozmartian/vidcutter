# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

cdef extern from "mpv/client.h":

    ctypedef signed char int8_t

    ctypedef short int16_t

    ctypedef int int32_t

    ctypedef long int64_t

    ctypedef unsigned char uint8_t

    ctypedef unsigned short uint16_t

    ctypedef unsigned int uint32_t

    ctypedef unsigned long uint64_t

    ctypedef signed char int_least8_t

    ctypedef short int_least16_t

    ctypedef int int_least32_t

    ctypedef long int_least64_t

    ctypedef unsigned char uint_least8_t

    ctypedef unsigned short uint_least16_t

    ctypedef unsigned int uint_least32_t

    ctypedef unsigned long uint_least64_t

    ctypedef signed char int_fast8_t

    ctypedef long int_fast16_t

    ctypedef long int_fast32_t

    ctypedef long int_fast64_t

    ctypedef unsigned char uint_fast8_t

    ctypedef unsigned long uint_fast16_t

    ctypedef unsigned long uint_fast32_t

    ctypedef unsigned long uint_fast64_t

    ctypedef long intptr_t

    ctypedef unsigned long uintptr_t

    ctypedef long intmax_t

    ctypedef unsigned long uintmax_t

    unsigned long mpv_client_api_version() nogil

    cdef struct mpv_handle:
        pass

    cdef enum mpv_error:
        MPV_ERROR_SUCCESS
        MPV_ERROR_EVENT_QUEUE_FULL
        MPV_ERROR_NOMEM
        MPV_ERROR_UNINITIALIZED
        MPV_ERROR_INVALID_PARAMETER
        MPV_ERROR_OPTION_NOT_FOUND
        MPV_ERROR_OPTION_FORMAT
        MPV_ERROR_OPTION_ERROR
        MPV_ERROR_PROPERTY_NOT_FOUND
        MPV_ERROR_PROPERTY_FORMAT
        MPV_ERROR_PROPERTY_UNAVAILABLE
        MPV_ERROR_PROPERTY_ERROR
        MPV_ERROR_COMMAND
        MPV_ERROR_LOADING_FAILED
        MPV_ERROR_AO_INIT_FAILED
        MPV_ERROR_VO_INIT_FAILED
        MPV_ERROR_NOTHING_TO_PLAY
        MPV_ERROR_UNKNOWN_FORMAT
        MPV_ERROR_UNSUPPORTED
        MPV_ERROR_NOT_IMPLEMENTED

    const char *mpv_error_string(int error) nogil

    void mpv_free(void *data) nogil

    const char *mpv_client_name(mpv_handle *ctx) nogil

    mpv_handle *mpv_create() nogil

    int mpv_initialize(mpv_handle *ctx) nogil

    void mpv_detach_destroy(mpv_handle *ctx) nogil

    void mpv_terminate_destroy(mpv_handle *ctx) nogil

    int mpv_load_config_file(mpv_handle *ctx, const char *filename) nogil

    void mpv_suspend(mpv_handle *ctx) nogil

    void mpv_resume(mpv_handle *ctx) nogil

    int64_t mpv_get_time_us(mpv_handle *ctx) nogil

    cdef enum mpv_format:
        MPV_FORMAT_NONE
        MPV_FORMAT_STRING
        MPV_FORMAT_OSD_STRING
        MPV_FORMAT_FLAG
        MPV_FORMAT_INT64
        MPV_FORMAT_DOUBLE
        MPV_FORMAT_NODE
        MPV_FORMAT_NODE_ARRAY
        MPV_FORMAT_NODE_MAP

    cdef struct ____mpv_node_u_mpv_node_list:
        pass

    ctypedef ____mpv_node_u_mpv_node_list ____mpv_node_u_mpv_node_list_t

    cdef union __mpv_node_u:
        char *string
        int flag
        int64_t int64
        double double_
        mpv_node_list *list

    ctypedef __mpv_node_u __mpv_node_u_t

    cdef struct mpv_node:
        __mpv_node_u_t u
        mpv_format format

    cdef struct mpv_node_list:
        int num
        mpv_node *values
        char **keys

    void mpv_free_node_contents(mpv_node *node) nogil

    int mpv_set_option(mpv_handle *ctx, const char *name, mpv_format format, void *data) nogil

    int mpv_set_option_string(mpv_handle *ctx, const char *name, const char *data) nogil

    int mpv_command(mpv_handle *ctx, const char **args) nogil

    int mpv_command_node(mpv_handle *ctx, mpv_node *args, mpv_node *result) nogil

    int mpv_command_string(mpv_handle *ctx, const char *args) nogil

    int mpv_command_async(mpv_handle *ctx, uint64_t reply_userdata, const char **args) nogil

    int mpv_command_node_async(mpv_handle *ctx, uint64_t reply_userdata, mpv_node *args) nogil

    int mpv_set_property(mpv_handle *ctx, const char *name, mpv_format format, void *data) nogil

    int mpv_set_property_string(mpv_handle *ctx, const char *name, const char *data) nogil

    int mpv_set_property_async(mpv_handle *ctx, uint64_t reply_userdata, const char *name, mpv_format format, void *data) nogil

    int mpv_get_property(mpv_handle *ctx, const char *name, mpv_format format, void *data) nogil

    char *mpv_get_property_string(mpv_handle *ctx, const char *name) nogil

    char *mpv_get_property_osd_string(mpv_handle *ctx, const char *name) nogil

    int mpv_get_property_async(mpv_handle *ctx, uint64_t reply_userdata, const char *name, mpv_format format) nogil

    int mpv_observe_property(mpv_handle *mpv, uint64_t reply_userdata, const char *name, mpv_format format) nogil

    int mpv_unobserve_property(mpv_handle *mpv, uint64_t registered_reply_userdata) nogil

    enum mpv_event_id:
        MPV_EVENT_NONE
        MPV_EVENT_SHUTDOWN
        MPV_EVENT_LOG_MESSAGE
        MPV_EVENT_GET_PROPERTY_REPLY
        MPV_EVENT_SET_PROPERTY_REPLY
        MPV_EVENT_COMMAND_REPLY
        MPV_EVENT_START_FILE
        MPV_EVENT_END_FILE
        MPV_EVENT_FILE_LOADED
        MPV_EVENT_TRACKS_CHANGED
        MPV_EVENT_TRACK_SWITCHED
        MPV_EVENT_IDLE
        MPV_EVENT_PAUSE
        MPV_EVENT_UNPAUSE
        MPV_EVENT_TICK
        MPV_EVENT_SCRIPT_INPUT_DISPATCH
        MPV_EVENT_CLIENT_MESSAGE
        MPV_EVENT_VIDEO_RECONFIG
        MPV_EVENT_AUDIO_RECONFIG
        MPV_EVENT_METADATA_UPDATE
        MPV_EVENT_SEEK
        MPV_EVENT_PLAYBACK_RESTART
        MPV_EVENT_PROPERTY_CHANGE
        MPV_EVENT_CHAPTER_CHANGE

    const char *mpv_event_name(mpv_event_id event) nogil

    cdef struct mpv_event_property:
        const char *name
        mpv_format format
        void *data

    enum mpv_log_level:
        MPV_LOG_LEVEL_NONE
        MPV_LOG_LEVEL_FATAL
        MPV_LOG_LEVEL_ERROR
        MPV_LOG_LEVEL_WARN
        MPV_LOG_LEVEL_INFO
        MPV_LOG_LEVEL_V
        MPV_LOG_LEVEL_DEBUG
        MPV_LOG_LEVEL_TRACE

    cdef struct mpv_event_log_message:
        const char *prefix
        const char *level
        const char *text
        int log_level

    enum mpv_end_file_reason:
        MPV_END_FILE_REASON_EOF
        MPV_END_FILE_REASON_STOP
        MPV_END_FILE_REASON_QUIT
        MPV_END_FILE_REASON_ERROR

    cdef struct mpv_event_end_file:
        int reason
        int error

    cdef struct mpv_event_script_input_dispatch:
        int arg0
        const char *type

    cdef struct mpv_event_client_message:
        int num_args
        const char **args

    cdef struct mpv_event:
        mpv_event_id event_id
        int error
        uint64_t reply_userdata
        void *data

    int mpv_request_event(mpv_handle *ctx, mpv_event_id event, int enable) nogil

    int mpv_request_log_messages(mpv_handle *ctx, const char *min_level) nogil

    mpv_event *mpv_wait_event(mpv_handle *ctx, double timeout) nogil

    void mpv_wakeup(mpv_handle *ctx) nogil

    void mpv_set_wakeup_callback(mpv_handle *ctx, void (*cb)(void *), void *d) nogil

    int mpv_get_wakeup_pipe(mpv_handle *ctx) nogil

    void mpv_wait_async_requests(mpv_handle *ctx) nogil

    enum mpv_sub_api:
        MPV_SUB_API_OPENGL_CB

    void *mpv_get_sub_api(mpv_handle *ctx, mpv_sub_api sub_api) nogil

cdef extern from "mpv/opengl_cb.h":
    struct mpv_opengl_cb_context:
        pass

    ctypedef void (*mpv_opengl_cb_update_fn)(void *cb_ctx)
    ctypedef void *(*mpv_opengl_cb_get_proc_address_fn)(void *fn_ctx,
                                                        const char *name) nogil

    void mpv_opengl_cb_set_update_callback(mpv_opengl_cb_context *ctx,
                                           mpv_opengl_cb_update_fn callback,
                                           void *callback_ctx) nogil

    int mpv_opengl_cb_init_gl(mpv_opengl_cb_context *ctx, const char *exts,
                              mpv_opengl_cb_get_proc_address_fn get_proc_address,
                              void *get_proc_address_ctx) nogil

    int mpv_opengl_cb_draw(mpv_opengl_cb_context *ctx, int fbo, int w, int h) nogil

    int mpv_opengl_cb_report_flip(mpv_opengl_cb_context *ctx, int64_t time) nogil

    int mpv_opengl_cb_uninit_gl(mpv_opengl_cb_context *ctx) nogil
