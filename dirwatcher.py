# !/usr/bin/env python
# -*- coding: utf-8 -*-
import signal
import time
import logging
import logging.handlers
# import handlers to handing logging
from datetime import datetime as dt
import argparse
import os
import errno
# import the error numbers so we can handle them
import sys

__author__ = "Paul Racisz + Chris Warren"

# variable for logging a file __file__ is passing in
# to log that file
logger = logging.getLogger(__file__)
# files dictionary
files = {}
# flag to exit the program
exit_flag = False


def watch_dir(args):
    """
    Look at the directory that you're watching
    Get a list of files
    Add files to files dictionary if they're not already in it
    Log a message if you're adding something to dictionary that's not already
    there--log as a new file
    Look through files dictionary and compare that to the list of
    files in the directory
    If file is not in your dictionary anymore you have to log that you removed
    the file from your dictionary
    """
    # grabbing all the files and putting them in a list.
    file_list = os.listdir(args.path)

    for f in file_list:
        # if file is not in file_list add to watch list.
        if f.endswith(args.ext) and f not in files:
            files[f] = 0
            logger.info(f"{f} added to watchlist.")
    # takes all the files and convert them into a mutable list.
    for f in list(files):
        # checking to see if a file got deleted or moved out directory.
        if f not in file_list:
            # once file is done being watch remove from watchlist.
            logger.info(f"{f} removed from watchlist.")
            del files[f]
    for f in files:
        files[f] = find_magic(
            # is the magic text in there?
            os.path.join(args.path, f),
            files[f],
            args.magic
        )


def find_magic(filename, starting_line, magic_word):
    """
    # Iterate through dictionary and open up each file at the last line that
    # you read from to see if there's anymore "magic" text
    # Update the last position you read from int he dictionary
    # Key will be the filenames and the values will be the starting line you
    # used and the last position you read from
    """
    # start looking for magic at line 0.
    line_number = 0
    # open the file to look for magic.
    with open(filename) as f:
        # enumerate through each line.
        for line_number, line in enumerate(f):
            if line_number >= starting_line:
                # if we find the magic_word in the line
                if magic_word in line:
                    # adding to our info text where we found the line, and
                    # add 1 so its human readable.
                    logger.info(
                        f"This file: {filename} "
                        f"found:  {magic_word} "
                        f"on line: {line_number + 1}"
                    )
    # humans start counting at 0, machines start at 1, hence the + 1.
    return line_number + 1


def signal_handler(sig_num, frame):
    """
    This is a handler for SIGTERM and SIGINT. Other signals
    can be mapped here as well (SIGHUP?)
    Basically it just sets a global flag, and main() will exit it's loop if
    the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """
    # Logs associated signal name (the python2 way)
    signames = dict((k, v) for v, k in
                    reversed(sorted(signal.__dict__.items()))
                    if v.startswith('SIG') and not v.startswith('SIG_'))
    # print out the signal with the signal number we imported above
    logger.warning('Received ' + signames[sig_num])
    global exit_flag
    exit_flag = True


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--ext', type=str, default='.txt',
                        help='Text file extension to watch')
    parser.add_argument('-i', '--interval', type=float, default=1.0,
                        help='Number of seconds between polling')
    parser.add_argument('path', help='Directory path to watch')
    parser.add_argument('magic', help='String to watch for')
    return parser


def main(args):
    """Runs the main function."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(name)-12s '
               '%(levelname)-8s %(message)s',
        datefmt='%m-%d-%Y &%H:%M:%S'
    )
    logger.setLevel(logging.DEBUG)
    app_start_time = dt.now()
    logger.info(
        '\n'
        '-------------------------------------------------\n'
        '   Running {0}\n'
        '   Started on {1}\n'
        '-------------------------------------------------\n'
        .format(__file__, app_start_time.isoformat())
    )
    # logger info is plugging in command line arguments.
    logger.info(f'Watching directory: {parsed_args.path}, '
                f'File Extension: {parsed_args.ext}, '
                f'Polling Interval: {parsed_args.interval}, '
                f'Magic Text: {parsed_args.magic}')

    # Connect these two signals from the OS
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # signal_handler will get called if OS sends either of these
    while not exit_flag:
        try:
            # Call to watch_dir Function
            watch_dir(parsed_args)
        except OSError as e:
            # UNHANDLED exception
            # Log an ERROR level message here
            if e.errno == errno.ENOENT:
                logger.error(f"{parsed_args.path} directory not found")
                time.sleep(2)
            else:
                logger.error(e)
        except Exception as e:
            logger.error(f"UNHANDLED EXCEPTION:{e}")
        # Sleeps while loop so cpu usage isn't at 100%
        time.sleep(int(float(parsed_args.interval)))
    # Final exit point
    # Logs a message that program is shutting down
    # Overall uptime since program start
    uptime = dt.now() - app_start_time
    logger.info(
           '\n'
           '-------------------------------------------------\n'
           '   Stopped {}\n'
           '   Uptime was {}\n'
           '-------------------------------------------------\n'
           .format(__file__, str(uptime))
           )
    logging.shutdown()


if __name__ == "__main__":
    main(sys.argv[1:])
