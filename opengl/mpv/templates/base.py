class AbstractTemplate(object):
    _handlers = ['on_none', 'on_shutdown', 'on_log_message',
                 'on_get_property_reply', 'on_set_property_reply',
                 'on_command_reply', 'on_start_file', 'on_end_file',
                 'on_file_loaded', 'on_tracks_changed', 'on_track_switched',
                 'on_idle', 'on_pause', 'on_unpause', 'on_tick',
                 'on_script_input_dispatch', 'on_client_message',
                 'on_video_reconfig', 'on_audio_reconfig',
                 'on_metadata_update', 'on_seek', 'on_playback_restart',
                 'on_property_change', 'on_chapter_change', 'on_queue_overflow']

    def _handle_event(self, event):
        handler = getattr(
            self, self._handlers[event.event_id.value], None)
        if not handler:
            return
        if event.data:
            handler(event.data)
        else:
            handler()

    def before_initialize(self):
        """ """
        pass

    def on_none(self):
        """ """
        pass

    def on_shutdown(self):
        """ """
        pass

    def on_log_message(self, event):
        """
        Args:
            event (:obj:`mpv.events.LogMessage`): the event data.

        """
        if self.log_handler:
            self.log_handler('{e.prefix}: {e.text}'.format(e=event))

    def on_get_property_reply(self, event):
        """
        Args:
            event (:obj:`mpv.events.Property`): the event data.

        """
        pass

    def on_set_property_reply(self):
        """ """
        pass

    def on_command_reply(self):
        """ """
        pass

    def on_start_file(self):
        """ """
        pass

    def on_end_file(self, event):
        """
        Args:
            event (:obj:`mpv.events.EndFile`): the event data.

        """
        pass

    def on_file_loaded(self):
        """ """
        pass

    def on_tracks_changed(self):
        """Deprecated."""
        pass

    def on_track_switched(self):
        """Deprecated."""
        pass

    def on_idle(self):
        """ """
        pass

    def on_pause(self):
        """Deprecated."""
        pass

    def on_unpause(self):
        """Deprecated."""
        pass

    def on_tick(self):
        """ """
        pass

    def on_script_input_dispatch(self):
        """Deprecated."""
        pass

    def on_client_message(self, event):
        """
        Args:
            event (:obj:`mpv.events.ClientMessage`): the event data.

        """
        pass

    def on_video_reconfig(self):
        """ """
        pass

    def on_audio_reconfig(self):
        """ """
        pass

    def on_metadata_update(self):
        """Deprecated."""
        pass

    def on_seek(self):
        """ """
        pass

    def on_playback_restart(self):
        """ """
        pass

    def on_property_change(self, event):
        """This method is called when the value of an observed property is
        changed. Reimplement this function in a subclass to handle the
        different properties.

        Args:
            event (:obj:`mpv.events.Property`): the event data.

        """
        pass

    def on_chapter_change(self):
        """Deprecated."""
        pass

    def on_queue_overflow(self):
        """ """
        pass
