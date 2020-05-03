from typing import List

from als_to_midi import automation_curve, MidiFile, models


def get_automation_events(events) -> List[dict]:
    automation_events = []
    count = 0
    quantize = 1 / 64
    for event in events:
        event_time = event.time if event.time >= 0 else 0
        event_value = event.value
        event_ccx = event.cc_x
        event_ccy = event.cc_y
        if event.type == 'init' or event.type == 'break' or event.type == 'EndCurve':
            automation_events.append({'Time': event_time, 'Value': event_value})

        elif event.type == 'affine':
            previous_event = events[count - 1]
            points = automation_curve.affine(previous_event.time,
                                             previous_event.value,
                                             event_time,
                                             event_value, quantize)
            for p in points:
                automation_events.append(
                    {'Time': points[p]['Time'], 'Value': points[p]['Value']})

        elif event.type == 'bCurve':
            next_event = events[count + 1]
            points = automation_curve.b_curve(event_time, event_value,
                                              next_event.time,
                                              next_event.value,
                                              event_ccx, event_ccy, quantize)
            for p in points:
                automation_events.append(
                    {'Time': points[p]['Time'], 'Value': points[p]['Value']})

        elif event.type == 'affine & bCurve':
            previous_event = events[count - 1]
            points = automation_curve.affine(previous_event.time,
                                             previous_event.value,
                                             event_time,
                                             event_value, quantize)
            for p in points:
                automation_events.append(
                    {'Time': points[p]['Time'], 'Value': points[p]['Value']})
            next_event = events[count + 1]
            points = automation_curve.b_curve(event_time, event_value,
                                              next_event.time,
                                              next_event.value,
                                              event_ccx, event_ccy, quantize)
            for p in points:
                automation_events.append(
                    {'Time': points[p]['Time'], 'Value': points[p]['Value']})

        count += 1

    return automation_events


def midi_export(live_set: models.LiveSet, midi_file_path: str,
                separate_channels: bool = False) -> None:
    print('Init Midi Export')
    # How Many Midi Tracks in liveSet?
    used_midi_track = 0
    for track in live_set.tracks:
        if len(track.notes) != 0:
            used_midi_track += 1
    # print ("Used Midi Track count:", used_midi_track)

    # Create the MIDIFile Object with 1 track
    my_midi = MidiFile.MIDIFile(len(live_set.tracks), file_format=1,
                                adjust_origin=True)

    i = 0
    for track in live_set.tracks:
        # Tracks are numbered from zero. Times are measured in beats.
        if track.midi_export:  # len(track.notes) != 0 and
            track_id = i
            channel = i % 16 if separate_channels else 0
            time = 0

            # Add track name.
            name = str(track.name)
            my_midi.addTrackName(track_id, time, name)

            # Add tempo Map to first track.
            if track_id == 0:
                events = get_automation_events(live_set.tempo_map)
                for event in events:
                    my_midi.addTempo(track_id, event['Time'], event['Value'])

            # Add Notes.
            for note in track.notes:
                pitch = note.pitch
                time = note.start
                duration = note.duration
                volume = note.velocity

                my_midi.addNote(track_id, channel, pitch, time, duration,
                                volume)

            # Add Clip Automations to MidiTrack
            for clip in track.arrangement_clips:
                for envelope in clip.envelopes:
                    events = get_automation_events(envelope.events)
                    target = envelope.target_name
                    for event in events:
                        time = event['Time'] + clip.start_time - clip.loop_start
                        value = int(event['Value'])
                        # print('time:{}, value:{}'.format(time, value))

                        if target == 'Pitch Bend':
                            my_midi.addPitchWheelEvent(track_id, channel,
                                                       time,
                                                       value)
                            print(time, value)
                        elif target == 'Channel Pressure':
                            my_midi.addChannelPressureEvent(track_id,
                                                            channel,
                                                            time, value)

                        # Prevent CC7(Volume) and CC10(Pan) Conflicts
                        elif int(target) != 7 and int(target) != 10:
                            my_midi.addControllerEvent(track_id, channel,
                                                       time,
                                                       int(target), value)

                        if isinstance(target, int) and int(
                                target) == 7 and not track.volume_midi_export:
                            my_midi.addControllerEvent(track_id, channel,
                                                       time,
                                                       int(target), value)

                        if isinstance(target, int) and int(
                                target) == 10 and not track.pan_midi_export:
                            my_midi.addControllerEvent(track_id, channel,
                                                       time,
                                                       int(target), value)

            i += 1

            # Add Volume Automation to Track
            if track.volume_midi_export:
                events = get_automation_events(track.volume_automation_events)
                for event in events:
                    time = event['Time']
                    value = event['Value']

                    # Scale value [0, 1] to [0, 100] and [1, 2] and [100, 127]
                    if value <= 1:
                        value = int(value * 100)
                    else:
                        value = int(100 + value * 28 / 2)
                    # print('time:', time, 'value:', value)
                    my_midi.addControllerEvent(track_id, channel, time, 7,
                                               value)

            # Add Pan Automation to Track
            if track.pan_midi_export:
                events = get_automation_events(track.pan_automation_events)
                for event in events:
                    time = event['Time']
                    value = event['Value']
                    # Scale value [-1, 1] to [0, 127]
                    value = int((value + 1) * 64)
                    my_midi.addControllerEvent(track_id, channel, time, 10,
                                               value)

    # And write it to disk.
    with open(midi_file_path, 'wb+') as bin_file:
        my_midi.writeFile(bin_file)
    print('Midi Export Done')


def main(als_file: str, midi_file: str):
    live_set = models.LiveSet(als_file)
    midi_export(live_set, midi_file, separate_channels=True)
