#!/usr/bin/env python3
import argparse

from als_to_midi import __description__
from als_to_midi.midi_export import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__description__)
    parser.add_argument('als_file', type=str, help='input ALS file')
    parser.add_argument('midi_file', type=str, help='output MIDI file')

    args = parser.parse_args()

    main(args.als_file, args.midi_file)
