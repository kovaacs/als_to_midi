#!/usr/bin/env python3
import argparse

from als_to_midi import __description__
from als_to_midi.models import LiveSet
from als_to_midi.midi_export import midi_export


def main(als_file: str, midi_file: str):
    live_set = LiveSet(als_file)
    midi_export(live_set, midi_file, separate_channels=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__description__)
    parser.add_argument('als_file', type=str, help='input ALS file')
    parser.add_argument('midi_file', type=str, help='output MIDI file')

    args = parser.parse_args()

    main(args.als_file, args.midi_file)
