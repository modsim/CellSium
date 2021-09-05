# noinspection PyPep8Naming
import xml.etree.ElementTree as ET
from pathlib import Path

from tunable import Tunable

from ..parameters import Calibration, Height, Width, um_to_pixel
from . import Output, check_overwrite, ensure_path_and_extension


class TrackMateXMLExportFluorescences(Tunable):
    """Names for the fluorescences for the JuNGLE TrackMate format"""

    # default = ''
    default = 'Crimson,YFP'


class TrackMateXMLExportLengthTypo(Tunable):
    """Whether to output in the classic JuNGLE TrackMate format"""

    default = True


EMPTY_TRACKMATE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<TrackMate version="2.7.3">
  <Settings>
    <ImageData filename="FILENAME" folder="" width="1" height="1" nslices="1" nframes="2" pixelwidth="1.0" 
    pixelheight="1.0" voxeldepth="1.0" timeinterval="1.0" />
    <BasicSettings xstart="0" xend="1" ystart="0" yend="1" zstart="0" zend="0" tstart="0" tend="2" />
<InitialSpotFilter feature="QUALITY" value="0.0" isabove="true" />
    <DetectorSettings DETECTOR_NAME="OVERLAY_DETECTOR" TARGET_CHANNEL="1" />
    <SpotFilterCollection />
    <TrackerSettings TRACKER_NAME="SPARSE_LAP_TRACKER" CUTOFF_PERCENTILE="0.9"
    ALTERNATIVE_LINKING_COST_FACTOR="1.05" BLOCKING_VALUE="Infinity">
      <Linking LINKING_MAX_DISTANCE="15.0">
        <FeaturePenalties />
      </Linking>
      <GapClosing ALLOW_GAP_CLOSING="true" GAP_CLOSING_MAX_DISTANCE="6.0" MAX_FRAME_GAP="2">
        <FeaturePenalties />
      </GapClosing>
      <TrackSplitting ALLOW_TRACK_SPLITTING="true" SPLITTING_MAX_DISTANCE="10.0">
        <FeaturePenalties />
      </TrackSplitting>
      <TrackMerging ALLOW_TRACK_MERGING="false" MERGING_MAX_DISTANCE="15.0">
        <FeaturePenalties />
      </TrackMerging>
    </TrackerSettings>
    <TrackFilterCollection />
    <AnalyzerCollection>
      <SpotAnalyzers>
        <Analyzer key="SPOT_FLUORESCENCE_ANALYZER" />
        <Analyzer key="SPOT_MEASUREMENT_ANALYZER" />
        <Analyzer key="MANUAL_SPOT_COLOR_ANALYZER" />
        <Analyzer key="Spot descriptive statistics" />
        <Analyzer key="Spot radius estimator" />
        <Analyzer key="Spot contrast and SNR" />
      </SpotAnalyzers>
      <EdgeAnalyzers>
        <Analyzer key="Edge target" />
        <Analyzer key="Edge mean location" />
        <Analyzer key="Edge velocity" />
        <Analyzer key="MANUAL_EDGE_COLOR_ANALYZER" />
      </EdgeAnalyzers>
      <TrackAnalyzers>
        <Analyzer key="Branching analyzer" />
        <Analyzer key="Track duration" />
        <Analyzer key="Track index" />
        <Analyzer key="Track location" />
        <Analyzer key="Velocity" />
        <Analyzer key="TRACK_SPOT_QUALITY" />
      </TrackAnalyzers>
    </AnalyzerCollection>
  </Settings>
  <Model spatialunits="pixels" timeunits="frames">
    <FeatureDeclarations>
      <SpotFeatures>
        <Feature feature="QUALITY" 
        name="Quality" shortname="Quality" dimension="QUALITY" isint="false" />
        <Feature feature="POSITION_X" 
        name="X" shortname="X" dimension="POSITION" isint="false" />
        <Feature feature="POSITION_Y" 
        name="Y" shortname="Y" dimension="POSITION" isint="false" />
        <Feature feature="POSITION_Z" 
        name="Z" shortname="Z" dimension="POSITION" isint="false" />
        <Feature feature="POSITION_T" 
        name="T" shortname="T" dimension="TIME" isint="false" />
        <Feature feature="FRAME" 
        name="Frame" shortname="Frame" dimension="NONE" isint="true" />
        <Feature feature="RADIUS" 
        name="Radius" shortname="R" dimension="LENGTH" isint="false" />
        <Feature feature="VISIBILITY" 
        name="Visibility" shortname="Visibility" dimension="NONE" isint="true" />
        <Feature feature="PIXELS" 
        name="Pixels" shortname="Pixels" dimension="INTENSITY" isint="false" />
        <Feature feature="AREA" 
        name="Cell area" shortname="Area" dimension="INTENSITY_SQUARED" isint="false" />
        <Feature feature="LENGHT" 
        name="Cell length" shortname="Length" dimension="LENGTH" isint="false" />
      </SpotFeatures>
      <EdgeFeatures>
        <Feature feature="SPOT_SOURCE_ID" name="Source spot ID" shortname="Source ID" dimension="NONE" isint="true" />
        <Feature feature="SPOT_TARGET_ID" name="Target spot ID" shortname="Target ID" dimension="NONE" isint="true" />
        <Feature feature="LINK_COST" name="Link cost" shortname="Cost" dimension="NONE" isint="false" />
      </EdgeFeatures>
      <TrackFeatures>
        <Feature feature="TRACK_INDEX" name="Track index" shortname="Index" dimension="NONE" isint="true" />
        <Feature feature="TRACK_ID" name="Track ID" shortname="ID" dimension="NONE" isint="true" />
      </TrackFeatures>
    </FeatureDeclarations>
    <AllSpots nspots="0">
    </AllSpots>
    <AllTracks>
    </AllTracks>
    <FilteredTracks>
    </FilteredTracks>
  </Model>
  <GUIState state="ConfigureViews">
    <View key="HYPERSTACKDISPLAYER" />
  </GUIState>
</TrackMate>
"""  # noqa


class TrackMateXML(Output):
    def __init__(self):
        super().__init__()

        self.root = ET.fromstring(EMPTY_TRACKMATE_XML)

        self.xml = ET.ElementTree(self.root)

        data = self.root.find('Settings/ImageData').attrib
        data['width'] = str(int(um_to_pixel(Width.value)))
        data['height'] = str(int(um_to_pixel(Height.value)))
        data['pixelwidth'] = str(Calibration.value)
        data['pixelheight'] = str(Calibration.value)

        self.image_data = data

        settings = self.root.find('Settings/BasicSettings').attrib

        settings['xend'] = str(int(um_to_pixel(Width.value)))
        settings['yend'] = str(int(um_to_pixel(Height.value)))

        spot_features = self.root.find('Model/FeatureDeclarations/SpotFeatures')

        for f in TrackMateXMLExportFluorescences.value.split(','):
            if not f:
                continue
            ET.SubElement(spot_features, 'Feature').attrib.update(
                dict(
                    feature='%s_FLUORESCENCE_MEAN' % f.upper(),
                    name='%s Mean' % f,
                    shortname='%s' % f,
                    dimension='INTENSITY',
                    isint='false',
                )
            )

            ET.SubElement(spot_features, 'Feature').attrib.update(
                dict(
                    feature='%s_FLUORESCENCE_STDDEV' % f.upper(),
                    name='%s StdDev' % f,
                    shortname='%s SD' % f,
                    dimension='INTENSITY',
                    isint='false',
                )
            )

            ET.SubElement(spot_features, 'Feature').attrib.update(
                dict(
                    feature='%s_FLUORESCENCE_TOTAL' % f.upper(),
                    name='%s Total' % f,
                    shortname='%sTot' % f,
                    dimension='INTENSITY',
                    isint='false',
                )
            )

        if not TrackMateXMLExportLengthTypo.value:
            for feature in spot_features:
                if feature.attrib['feature'] == 'LENGHT':
                    feature.attrib['feature'] = 'LENGTH'

        self.basic_settings = settings

        self.frame_counter = 0

        self.all_spots = self.root.find('Model/AllSpots')
        self.spot_counter = 0

        self.cell_to_spot = {}
        self.spot_to_cell = {}
        self.id_to_cell = {}

        self.tracks = {}
        self.track_counter = 0

        self.all_tracks = self.root.find('Model/AllTracks')
        self.filtered_tracks = self.root.find('Model/FilteredTracks')

    def output(self, world, time=0.0, **kwargs):
        frame_counter = self.frame_counter

        self.frame_counter += 1

        self.image_data['nframes'] = str(frame_counter)
        self.basic_settings['tend'] = str(frame_counter)

        # frame
        group = ET.SubElement(self.all_spots, 'SpotsInFrame')
        group.attrib['frame'] = str(frame_counter)

        def add_track():
            elem = ET.SubElement(self.all_tracks, 'Track')
            self.track_counter += 1
            track_count = self.track_counter
            elem.attrib['name'] = 'Track_' + str(track_count)
            elem.attrib['TRACK_INDEX'] = str(track_count)
            elem.attrib['TRACK_ID'] = str(track_count)

            the_elem = elem

            elem = ET.SubElement(self.filtered_tracks, 'TrackID')
            elem.attrib['TRACK_ID'] = str(track_count)

            return the_elem

        def connect(track, from_, to_):
            elem = ET.SubElement(track, 'Edge')

            elem.attrib['SPOT_SOURCE_ID'] = str(from_)
            elem.attrib['SPOT_TARGET_ID'] = str(to_)

            elem.attrib['LINK_COST'] = str(1.0)

        old_cell_to_spot = self.cell_to_spot.copy()
        old_id_to_cell = self.id_to_cell.copy()

        for cell in world.cells:
            self.spot_counter += 1
            self.cell_to_spot[cell] = self.spot_counter
            self.spot_to_cell[self.spot_counter] = cell
            self.id_to_cell[cell.id_] = cell

        # # when dealing with local history sequences
        # def sub_sequences(seq):
        #     for n in range(len(seq)):
        #         yield seq[n:]

        for cell in world.cells:
            spot = ET.SubElement(group, 'Spot')

            # history = tuple(cell.lineage_history[::-1])
            # this will probably not work if more than one division
            # is between xml-write intervals

            if cell in self.tracks:
                connect(
                    self.tracks[cell], old_cell_to_spot[cell], self.cell_to_spot[cell]
                )
            else:
                if (
                    cell.parent_id in old_id_to_cell
                    and old_id_to_cell[cell.parent_id] in self.tracks
                ):
                    connect(
                        self.tracks[old_id_to_cell[cell.parent_id]],
                        old_cell_to_spot[old_id_to_cell[cell.parent_id]],
                        self.cell_to_spot[cell],
                    )
                    self.tracks[cell] = self.tracks[old_id_to_cell[cell.parent_id]]
                else:
                    self.tracks[cell] = add_track()

            spot.attrib['ID'] = str(self.cell_to_spot[cell])
            spot.attrib['name'] = str(self.cell_to_spot[cell])

            for f in TrackMateXMLExportFluorescences.value.split(','):
                if not f:
                    continue

                spot.attrib['%s_FLUORESCENCE_TOTAL' % f.upper()] = '0.0'
                spot.attrib['%s_FLUORESCENCE_MEAN' % f.upper()] = '0.0'
                spot.attrib['%s_FLUORESCENCE_STDDEV' % f.upper()] = '0.0'

            spot.attrib['AREA'] = str(0.0)
            spot.attrib['VISIBILITY'] = str(1)

            spot.attrib['POSITION_T'] = str(time)  # minutes or seconds?

            if not TrackMateXMLExportLengthTypo.value:
                spot.attrib['LENGTH'] = str(cell.length)
            else:
                spot.attrib['LENGHT'] = str(cell.length)  # sic!

            spot.attrib['PIXELS'] = str(0.0)

            spot.attrib['POSITION_X'] = str(um_to_pixel(cell.position[0]))
            spot.attrib['POSITION_Y'] = str(
                um_to_pixel(Height.value - cell.position[1])
            )
            spot.attrib['POSITION_Z'] = str(0.0)

            spot.attrib['FRAME'] = str(frame_counter)

            spot.attrib['RADIUS'] = str(5.0)
            spot.attrib['QUALITY'] = str(1.0)

        self.all_spots.attrib['nspots'] = str(self.spot_counter)

    # noinspection PyMethodOverriding
    def write(self, world, file_name, time=0.0, overwrite=False, **kwargs):
        self.output(world, time=time)

        self.image_data['filename'] = Path(
            ensure_path_and_extension(file_name, '.tif')
        ).name

        file_name = check_overwrite(
            ensure_path_and_extension(file_name, '.xml'), overwrite=overwrite
        )

        self.xml.write(file_name)

    def display(self, world, **kwargs):
        raise RuntimeError('Unsupported')


__all__ = ['TrackMateXML']
