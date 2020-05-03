import os
from typing import List

from lxml import etree as et

from als_to_midi import file_handler


class Envelope:
    def __init__(self, target_id=None, target_name=None, events=None):
        self.target_id = target_id
        self.target_name = target_name
        self.events = events

    def __repr__(self):
        return 'Envelope : targetName:{}, targetId:{} \nevents:{}'.format(
            self.target_name, self.target_id, self.events)


class Event:
    def __init__(self, time, value, cc_x, cc_y, previous_event=None):
        self.time = time
        self.value = value
        self.cc_x = cc_x
        self.cc_y = cc_y
        self.get_event_type(previous_event)

    def __repr__(self):
        #    if self.type is not 'bCurve':
        #        return 'type:{}, time:{}, value:{}'.format(self.type, self.time, self.value)
        #    else:
        return '\ntype:{}, time:{}, value:{}, ccX:{}, ccY:{}'.format(self.type,
                                                                     self.time,
                                                                     self.value,
                                                                     self.cc_x,
                                                                     self.cc_y)

    def get_event_type(self, previous_event=None):
        self.type = None
        if self.cc_x is not None and self.cc_y is not None:
            self.type = 'bCurve'
        elif self.cc_x is not None and self.cc_y is not None and previous_event.time != self.time and previous_event.value != self.value:
            self.type = 'affine & bCurve'
        elif previous_event is not None and previous_event.time == self.time:
            self.type = 'break'
        elif previous_event is not None and previous_event.time != self.time and previous_event.value != self.value and self.cc_x is None \
                and self.cc_y is None and previous_event.ccX is None and previous_event.ccY is None:
            self.type = 'affine'
        elif previous_event is not None and previous_event.time != self.time and self.cc_x is None and self.cc_y is None \
                and previous_event.ccX is not None and previous_event.ccY is not None and self.type is None:
            self.type = 'EndCurve'
        elif previous_event is None:
            self.type = 'init'


class Note:
    def __init__(self, pitch, time, duration, velocity, is_enable):
        self.pitch = int(pitch)
        self.start = float(time)
        self.duration = float(duration)
        self.velocity = int(float(velocity))
        self.is_enable = is_enable

    def __repr__(self):
        return f'\npitch: {str(self.pitch)} ' \
               f'time: {str(self.start)} ' \
               f'duration: {str(self.duration)} ' \
               f'velocity: {str(self.velocity)} ' \
               f'isEnable: {str(self.is_enable)}'


class MidiClip:
    def __init__(self, track, xml_clip):
        self.xml_clip = xml_clip
        self.track = track
        self.start_time = float(xml_clip.get('Time'))
        self.lom_id = int(xml_clip.find('LomId').get('Value'))
        self.name = xml_clip.find('Name').get('Value')
        self.color_index = int(xml_clip.find('ColorIndex').get('Value'))
        self.start = float(xml_clip.find('CurrentStart').get('Value'))
        self.end = float(xml_clip.find('CurrentEnd').get('Value'))
        self.loop_start = float(xml_clip.find('Loop/LoopStart').get('Value'))
        self.loop_end = float(xml_clip.find('Loop/LoopEnd').get('Value'))
        self.start_relative = float(
            xml_clip.find('Loop/StartRelative').get('Value'))
        self.loop = True if (xml_clip.find('Loop/LoopOn').get(
            'Value')) == 'true' else False
        self.time_signature_numerator = int(xml_clip.find(
            'TimeSignature/TimeSignatures/RemoteableTimeSignature/Numerator').get(
            'Value'))

        self.notes = self.parse_notes(xml_clip)
        self.envelopes = self.parse_envelopes(xml_clip)
        # print (self.envelopes)

    def __repr__(self):
        return f"Clip Name: {self.name}\n" \
               f"Start Time: {self.start_time}\n" \
               f"{self.notes}"

    def parse_notes(self, xml_clip):
        clip_notes = []
        pitches = xml_clip.findall('Notes/KeyTracks/KeyTrack')
        for p in pitches:
            pitch = p.find('MidiKey').get('Value')
            notes = p.findall('Notes/MidiNoteEvent')
            for n in notes:
                time = n.get("Time")
                duration = n.get("Duration")
                velocity = n.get("Velocity")
                is_enable = n.get("IsEnabled")
                note = Note(pitch, time, duration, velocity,
                            is_enable)
                clip_notes.append(note)
        '''
        for note in clip_notes:
            print note
        '''
        return clip_notes

    def parse_envelopes(self, xml_clip):
        # print('init parse Envelopes')
        clip_envelopes = []
        envelopes = xml_clip.findall('Envelopes/Envelopes/ClipEnvelope')
        for envelope in envelopes:
            if envelope is not None:
                # print('envelope found')
                target = int(
                    envelope.find('EnvelopeTarget/PointeeId').get('Value'))
                target_name = self.track.midi_controllers_map[target]
                float_events = []
                events = envelope.findall('Automation/Events/FloatEvent')
                for event in events:
                    time = float(event.get('Time'))
                    value = float(event.get('Value'))
                    cc_x = float(event.get('CurveControl1X')) if event.get(
                        'CurveControl1X') else None
                    cc_y = float(event.get('CurveControl1Y')) if event.get(
                        'CurveControl1Y') else None
                    count = len(float_events)
                    if count != 0:
                        e = Event(time, value, cc_x, cc_y,
                                  float_events[count - 1])
                    else:
                        e = Event(time, value, cc_x, cc_y)
                    float_events.append(e)
                clip_envelopes.append(
                    Envelope(target, target_name, float_events))

        return clip_envelopes


def get_automation_events(xml_path_parameter):
    float_events = []
    events = xml_path_parameter.findall(
        'ArrangerAutomation/Events/FloatEvent')
    for event in events:
        time = float(event.get('Time'))
        value = float(event.get('Value'))
        cc_x = float(event.get('CurveControl1X')) if event.get(
            'CurveControl1X') else None
        cc_y = float(event.get('CurveControl1Y')) if event.get(
            'CurveControl1Y') else None
        count = len(float_events)
        if count != 0:
            e = Event(time, value, cc_x, cc_y, float_events[count - 1])
        else:
            e = Event(time, value, cc_x, cc_y)
        float_events.append(e)
    return float_events


class MidiTrack:
    def __init__(self, xml_track):
        self.xml_track = xml_track
        self.name = str(xml_track.find('Name/EffectiveName').get('Value'))
        self.id = int(xml_track.get('Id'))
        self.color_index = int(xml_track.find('ColorIndex').get('Value'))
        self.group_id = xml_track.find('TrackGroupId').get('Value')
        self.unfold = xml_track.find('TrackUnfolded').get('Value')
        self.midi_fold_in = xml_track.find('MidiFoldIn').get('Value')
        self.midi_prelisten = xml_track.find('MidiPrelisten').get('Value')
        self.freeze = xml_track.find('Freeze').get('Value')
        # self.sessionClips
        self.midi_controllers_map = self.map_controllers()
        self.arrangement_clips = self.parse_clips()
        self.notes = self.parse_notes()
        # print self.name
        # print self.notes

        # Midi Export Options
        self.midi_export = True
        self.volume_midi_export = True
        self.pan_midi_export = True

        # Track Mixer Parameters:
        self.volume_automation_events = get_automation_events(
            xml_track.find('DeviceChain/Mixer/Volume'))  # VolumePath
        self.pan_automation_events = get_automation_events(
            xml_track.find('DeviceChain/Mixer/Pan'))  # PanPath

    def __repr__(self):
        return "MidiTrack Name: {}\n{}\n".format(self.name,
                                                 self.arrangement_clips)

    def parse_clips(self):
        midi_clips = []
        for midi_clip in self.xml_track.findall(
                'DeviceChain/MainSequencer/ClipTimeable/ArrangerAutomation/Events/MidiClip'):
            if midi_clip is not None:
                midi_clips.append(MidiClip(self, midi_clip))
        return midi_clips

    def parse_notes(self):
        midi_notes = []
        for midi_clip in self.arrangement_clips:
            current_start = midi_clip.start
            current_end = midi_clip.end
            loop_start = midi_clip.loop_start
            loop_end = midi_clip.loop_end
            start_relative = midi_clip.start_relative
            length = current_end - current_start
            loop_length = loop_end - loop_start
            loop = midi_clip.loop
            for note in midi_clip.notes:
                start = current_start + note.start - loop_start - start_relative
                if current_start <= start < current_end:
                    note = Note(note.pitch, start, note.duration, note.velocity,
                                note.is_enable)
                    midi_notes.append(note)
                    if loop and length > loop_length - start_relative and loop_start <= note.start < loop_end:
                        # print('!clip is looping! Loop length:', loop_length)
                        while start < current_end:
                            # print('note Start:', start, 'end:', current_end)
                            note = Note(note.pitch, start, note.duration,
                                        note.velocity, note.is_enable)
                            midi_notes.append(note)
                            start += loop_length

                # case loop Note after start marker
                elif loop and loop_start <= note.start < loop_end:
                    # print(note)
                    start = current_start + note.start - loop_start - start_relative + loop_length
                    while start < current_end:
                        # print('note Start:', start, 'end:', current_end)
                        note = Note(note.pitch, start, note.duration,
                                    note.velocity, note.is_enable)
                        midi_notes.append(note)
                        start += loop_length

        return midi_notes

    def map_controllers(self):
        controllers_map = {}
        controllers_names = ["Pitch Bend", "Channel Pressure", "Bank Select",
                             "Modulation", "Breath", "(Controller)",
                             "Foot Pedal", "Portamento Time", "Data Entry",
                             "Volume", "Balance", "(Controller)", "Pan",
                             "Expression",
                             "Effect Control 1", "Effect Control 2",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "Hold Pedal",
                             "Portamento On/Off", "Sostenuto Pedal",
                             "Soft Pedal", "Legato Pedal", "Hold Pedal 2",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "Data Entry Increment", "Data Entry Decrement",
                             "NRPN LSB", "NRPN MSB", "RPN LSB", "RPN MSB",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)", "(Controller)",
                             "(Controller)", "(Controller)"]
        midi_controllers = self.xml_track.find(
            'DeviceChain/MainSequencer/MidiControllers')
        count = 0
        for midi_controller in midi_controllers.iterchildren():
            if count < 2:
                name = controllers_names[count]
            else:
                name = count - 2
            # print(self.name, name, midi_controller.tag, midi_controller.get('Id'))
            count += 1
            controllers_map[int(midi_controller.get('Id'))] = str(name)
        # print (controllers_map)
        return controllers_map


class LiveSet:
    def __init__(self, file_path: str, copy: bool = False) -> None:
        self.file_path = file_path
        self.name = os.path.basename(self.file_path).replace('.als', '')
        print("LiveSet", self.name)
        self.infos = file_handler.extract(str(file_path), copy)
        print('Init LiveSet Parse')
        parser = et.XMLParser(huge_tree=True)
        self.doc = et.fromstring(self.infos, parser)

        self.tempo = int(
            self.doc.find("LiveSet/MasterTrack/DeviceChain/Mixer/Tempo").find(
                'Manual').get('Value'))
        self.tempo_map = self.get_tempo_map()
        self.tracks = self.parse_tracks()
        print(len(self.tracks), "Midi Tracks found")
        print('Tempo Map', self.tempo_map)
        print('LiveSet Parse Done')

    def parse_tracks(self) -> List[MidiTrack]:
        midi_tracks = []
        for midi_track in self.doc.xpath("//MidiTrack"):
            track = MidiTrack(midi_track)
            midi_tracks.append(track)
        return midi_tracks

    def get_tempo_map(self) -> List[Event]:
        events = self.doc.findall(
            "LiveSet/MasterTrack/DeviceChain/Mixer/Tempo/ArrangerAutomation/Events/FloatEvent")
        float_events = []
        for event in events:
            time = float(event.get('Time'))
            value = int(float(event.get('Value')))
            cc_x = float(event.get('CurveControl1X')) if event.get(
                'CurveControl1X') else None
            cc_y = float(event.get('CurveControl1Y')) if event.get(
                'CurveControl1Y') else None
            count = len(float_events)
            if count != 0:
                e = Event(time, value, cc_x, cc_y,
                          float_events[count - 1])
            else:
                e = Event(time, value, cc_x, cc_y)
            float_events.append(e)

        return float_events
