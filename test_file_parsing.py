from xml.etree.ElementTree import ParseError

import fitdecode
import gzip
import os
import tcxparser
import xmltodict
import xml.etree.ElementTree as ET

def decompress_gz_file(input_file, output_file):
    print(f'input_file is: {input_file}')
    print(f'output_file is: {output_file}')
    with gzip.open(input_file, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            f_out.write(f_in.read())


# def get_activity_fit_file(activity_id, filepath):
#     filename = f'{activity_id}.fit.gz'
#     output_file = f'{activity_id}.fit'
#
#     count = 0
#     for file in os.listdir(input_file_path):
#         if file == filename:
#             filepath = os.path.join(input_file_path, file)
#             print(filepath)
#             break  # Stop searching once the file is found
#
#     decompress_gz_file(filepath, output_file)
#
#     with fitdecode.FitReader(output_file) as fit_file:
#         for frame in fit_file:
#             if isinstance(frame, fitdecode.FitDataMessage):
#                 if frame.name == 'record':
#                     # print(f'frame: {frame}')
#                     time = frame.get_value('timestamp')
#                     distance = frame.get_value('distance')
#                     altitude = frame.get_value('altitude')
#                     speed = frame.get_value('speed')
#                     heart_rate = frame.get_value('heart_rate')
#                     cadence = frame.get_value('cadence')
#                     temperature = frame.get_value('temperature')
#
#                     if heart_rate and speed:
#                         count += 1
#                         print(f'({count})Time: {time} - Heart Rate: {heart_rate} bpm - Speed: {speed} m/s')

# def modify_tcx_file(filepath, filename):
#     txt_file = f'{filename.split(".")[0]}.txt'
#     # output_file = filename
#     print(f'filepath is: {filepath}')
#     print(f'filename is: {filename}')
#     decompress_gz_file(f'{filepath}{filename}', f'{filename.split(".")[0]}.tcx')
#     print(f'tcx file is: {filename}')
#     print('filename head is:')
#     # os.system(f'head {filepath}{filename}')
#
#     try:
#         mytree = ET.parse(f'{filename.split(".")[0]}.tcx')
#     except ParseError as e:
#         print(e)
#     else:
#         myroot = mytree.getroot()
#
#     # print(f'myroot is: {myroot}')
#     with open(txt_file, "w") as f:
#         # count = 0
#         for element in myroot.iter():
#             if element.text:
#                 if element.tag.split('}')[-1] == 'Value':
#                     print(element.text.strip())
#                 # print(f'{element.tag.split("}")[-1]}: {element.text.strip()}\n')
#                 f.write(element.tag + ': ' + element.text.strip() + '\n')
#                 # f.write(element.text.strip() + '\n')
#
#
#     # os.system(f'head {filename}')
#     return

def get_activity_tcx_file(activity_id, input_file_path):

    filename = f'121477830.tcx.gz'
    output_file = filename.split('.gz')[0]
    # filename = f'118777434.tcx.gz'
    # output_file = f'118777434.tcx'
    # print(f'input_file_path is: {input_file_path}')
    # print(f'filename is: {filename}')
    # print(f'output_file is: {output_file}')
    for file in os.listdir(input_file_path):
        if file == filename:
            filepath = os.path.join(input_file_path, file)
            # print(f'It\'s a match! {filepath}')
            decompress_gz_file(f'{input_file_path}{filename}', output_file)
            with open(output_file, "r") as f:
                xml_string = f.read()  # Strip leading/trailing whitespace
                xml_dict = xmltodict.parse(xml_string)
                # print(f'f is: {xml_string}')
                # print('filename head is:')
                # os.system(f'head {filepath}{filename}')
                # Parse the TCX file
                tcx = tcxparser.TCXParser(xml_string)
                # tree = ET.fromstring(xml_string)
                # root = tree.getroot()

            break  # Stop searching once the file is found

    # # Parse the TCX file
    # tcx = tcxparser.TCXParser(output_file)

    # Access the activity data totals
    # print(tcx.activity_type)
    # print(tcx.started_at)
    # print(tcx.distance)
    # print(tcx.duration)
    # print(tcx.calories)
    # print(tcx.hr_avg)
    # print(tcx.hr_max)

    # Show activity data points
    print(tcx.altitude_points())
    print(tcx.distance_values())
    print(tcx.time_values())
    print(tcx.cadence_values())
    print(tcx.hr_values())
    print(tcx.position_values())
    print(tcx.power_values())

if __name__ == "__main__":

    # activity_id = '1297099' # .fit file
    activity_id = '108685060' # .tcx file
    input_file_path = f'export_Dec-01-2024/activities/'
    # input_file_path = f'export_Dec-01-2024/'

    # get_activity_fit_file(activity_id, input_file_path)
    get_activity_tcx_file(activity_id, input_file_path)
