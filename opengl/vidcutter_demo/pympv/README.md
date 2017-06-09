pympv
=====
A python wrapper for libmpv.

To use::

    import sys
    import mpv

    def main(args):
        if len(args) != 1:
            print('pass a single media file as argument')
            return 1

        try:
            m = mpv.Context()
        except mpv.MPVError:
            print('failed creating context')
            return 1

        m.set_option('input-default-bindings')
        m.set_option('osc')
        m.set_option('input-vo-keyboard')
        m.initialize()

        m.command('loadfile', args[0])

        while True:
            event = m.wait_event(.01)
            if event.id == mpv.Events.none:
                continue
            print(event.name)
            if event.id in [mpv.Events.end_file, mpv.Events.shutdown]:
                break

    if __name__ == '__main__':
        try:
            exit(main(sys.argv[1:]) or 0)
        except mpv.MPVError as e:
            print(str(e))
            exit(1)

libmpv is a client library for the media player mpv

For more info see: https://github.com/mpv-player/mpv/blob/master/libmpv/client.h
