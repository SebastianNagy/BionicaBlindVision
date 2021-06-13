#!/usr/bin/env python3
import colorsys
import logging
import os.path as osp
import random
import sys
from argparse import ArgumentParser, SUPPRESS
from time import perf_counter

import cv2
import numpy as np
from openvino.inference_engine import IECore

#sys.path.append(osp.join(osp.dirname(osp.dirname(osp.abspath(__file__))), 'common'))
sys.path.append("/home/pi/open_model_zoo/demos/python_demos/common")


from models import *
import monitors
from pipelines import AsyncPipeline
from performance_metrics import PerformanceMetrics

from face_detection import face_recog_compare
import datetime

logging.basicConfig(format='[ %(levelname)s ] %(message)s', level=logging.INFO, stream=sys.stdout)
log = logging.getLogger()


def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument('-m', '--model', help='Path to an .xml file with a trained model.',
                      type=str)
    args.add_argument('-at', '--architecture_type', help='Specify model\' architecture type.',
                      type=str, choices=('ssd', 'yolo', 'faceboxes', 'centernet', 'retina'))
    args.add_argument('-i', '--input',type=str,
                      help='Required. Path to an image, folder with images, video file or a numeric camera ID.')
    args.add_argument('-d', '--device', default='CPU', type=str,
                      help='Optional. Specify the target device to infer on; CPU, GPU, FPGA, HDDL or MYRIAD is '
                           'acceptable. The sample will look for a suitable plugin for device specified. '
                           'Default value is CPU.')

    common_model_args = parser.add_argument_group('Common model options')
    common_model_args.add_argument('--labels', help='Optional. Labels mapping file.', default=None, type=str)
    common_model_args.add_argument('-t', '--prob_threshold', default=0.5, type=float,
                                   help='Optional. Probability threshold for detections filtering.')
    common_model_args.add_argument('--keep_aspect_ratio', action='store_true', default=False,
                                   help='Optional. Keeps aspect ratio on resize.')

    infer_args = parser.add_argument_group('Inference options')
    infer_args.add_argument('-nireq', '--num_infer_requests', help='Optional. Number of infer requests',
                            default=1, type=int)
    infer_args.add_argument('-nstreams', '--num_streams',
                            help='Optional. Number of streams to use for inference on the CPU or/and GPU in throughput '
                                 'mode (for HETERO and MULTI device cases use format '
                                 '<device1>:<nstreams1>,<device2>:<nstreams2> or just <nstreams>).',
                            default='', type=str)
    infer_args.add_argument('-nthreads', '--num_threads', default=None, type=int,
                            help='Optional. Number of threads to use for inference on CPU (including HETERO cases).')

    io_args = parser.add_argument_group('Input/output options')
    io_args.add_argument('-loop', '--loop', help='Optional. Loops input data.', action='store_true', default=False)
    io_args.add_argument('-no_show', '--no_show', help="Optional. Don't show output.", action='store_true')
    io_args.add_argument('-u', '--utilization_monitors', default='', type=str,
                         help='Optional. List of monitors to show initially.')

    debug_args = parser.add_argument_group('Debug options')
    debug_args.add_argument('-r', '--raw_output_message', help='Optional. Output inference results raw values showing.',
                            default=False, action='store_true')
    return parser


class ColorPalette:
    def __init__(self, n, rng=None):
        assert n > 0

        if rng is None:
            rng = random.Random(0xACE)

        candidates_num = 100
        hsv_colors = [(1.0, 1.0, 1.0)]
        for _ in range(1, n):
            colors_candidates = [(rng.random(), rng.uniform(0.8, 1.0), rng.uniform(0.5, 1.0))
                                 for _ in range(candidates_num)]
            min_distances = [self.min_distance(hsv_colors, c) for c in colors_candidates]
            arg_max = np.argmax(min_distances)
            hsv_colors.append(colors_candidates[arg_max])

        self.palette = [self.hsv2rgb(*hsv) for hsv in hsv_colors]

    @staticmethod
    def dist(c1, c2):
        dh = min(abs(c1[0] - c2[0]), 1 - abs(c1[0] - c2[0])) * 2
        ds = abs(c1[1] - c2[1])
        dv = abs(c1[2] - c2[2])
        return dh * dh + ds * ds + dv * dv

    @classmethod
    def min_distance(cls, colors_set, color_candidate):
        distances = [cls.dist(o, color_candidate) for o in colors_set]
        return np.min(distances)

    @staticmethod
    def hsv2rgb(h, s, v):
        return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))

    def __getitem__(self, n):
        return self.palette[n % len(self.palette)]

    def __len__(self):
        return len(self.palette)


def get_model(ie, args):
    if args.architecture_type == 'ssd':
        return SSD(ie, args.model, labels=args.labels, keep_aspect_ratio_resize=args.keep_aspect_ratio)
    elif args.architecture_type == 'faceboxes':
        return FaceBoxes(ie, args.model, threshold=args.prob_threshold)
    else:
        raise RuntimeError('No model type or invalid model type (-at) provided: {}'.format(args.architecture_type))

def get_plugin_configs(device, num_streams, num_threads):
    config_user_specified = {}

    devices_nstreams = {}
    if num_streams:
        devices_nstreams = {device: num_streams for device in ['CPU', 'GPU'] if device in device} \
            if num_streams.isdigit() \
            else dict(device.split(':', 1) for device in num_streams.split(','))

    if 'CPU' in device:
        if num_threads is not None:
            config_user_specified['CPU_THREADS_NUM'] = str(num_threads)
        if 'CPU' in devices_nstreams:
            config_user_specified['CPU_THROUGHPUT_STREAMS'] = devices_nstreams['CPU'] \
                if int(devices_nstreams['CPU']) > 0 \
                else 'CPU_THROUGHPUT_AUTO'

    if 'GPU' in device:
        if 'GPU' in devices_nstreams:
            config_user_specified['GPU_THROUGHPUT_STREAMS'] = devices_nstreams['GPU'] \
                if int(devices_nstreams['GPU']) > 0 \
                else 'GPU_THROUGHPUT_AUTO'

    return config_user_specified

# Functia primeste o imagine, obiectele (sau fetele) detectate si le contureaza in imagine
def draw_detections(frame, detections, palette, labels, threshold, draw_landmarks=False, face_det=False, source_person=None, person_name = ""):
    frame_size = frame.shape[:2]
    detected_objects = []
    detected_boxes = []
    
    obj_dim_list = [0, 1600, 1000, 1200, 1000, 3000, 2500,
                    2500, 3000, 1000, 4000, 500, 0, 2500, 
                    1500, 1000, 200, 300, 500, 2000, 700, 1700, 
                    3000, 2000, 2000, 5000, 0, 440, 700, 0, 0, 
                    350, 400, 350, 200, 1700, 1800, 300, 
                    300, 500, 250, 700, 1700, 700, 
                    350, 0, 150, 150, 250, 250, 250, 100, 
                    180, 100, 70, 100, 70, 150, 150, 300, 
                    100, 150, 700, 700, 500, 1000, 0, 1200, 
                    0, 0, 600, 0, 440, 230, 100, 250, 200, 170, 
                    400, 1200, 200, 1200, 1700, 0, 220, 
                    250, 250, 200, 500, 400, 150]
    
    orig_frame = frame
    for detection in detections:
        if detection.score > threshold:
            xmin = max(int(detection.xmin), 0)
            ymin = max(int(detection.ymin), 0)
            xmax = min(int(detection.xmax), frame_size[1])
            ymax = min(int(detection.ymax), frame_size[0])
            class_id = int(detection.id)
            color = palette[class_id]
            
            if face_det == True:
                face = orig_frame[ymin:ymax, xmin:xmax]
                face = cv2.resize(face, (128,128))
                
                comp_start = datetime.datetime.now()
                result = face_recog_compare(source_person, face)[0]
                comp_end = datetime.datetime.now()
                a = comp_end - comp_start
                print(f"[ METRICS ] Comparison took {a.seconds}s and {a.microseconds / 1000}ms.")
                
                if result == True:
                    obj_dim = 150
                    det_label = labels[class_id] if labels and len(labels) >= class_id else '#{}'.format(class_id)
                    detected_objects.append(det_label)
                    distance = (3.14 * frame_size[0] * obj_dim) / ((ymax-ymin) * 2.76)
                    detected_boxes.append((int(xmin + (xmax-xmin)/2), int(ymin + (ymax-ymin)/2), distance))
                
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (255, 255, 255), 2)
                    cv2.putText(frame, f"{person_name} {result} " + "{:.1%}".format( detection.score),
                        (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 255, 255), 1)
                else:
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (255, 255, 255), 2)
                    cv2.putText(frame, f"{person_name} {result} " + "{:.1%}".format( detection.score),
                        (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 255, 255), 1)
            else:
                obj_dim = obj_dim_list[class_id]
                det_label = labels[class_id] if labels and len(labels) >= class_id else '#{}'.format(class_id)
                detected_objects.append(det_label)
                distance = (3.14 * frame_size[0] * obj_dim) / ((ymax-ymin) * 2.76)
                
                print(f"{det_label} dimension is {obj_dim} - size is {frame_size[0]} - obj pixel size is {ymax-ymin}  --> distance = {distance}mm")
                detected_boxes.append((int(xmin + (xmax-xmin)/2), int(ymin + (ymax-ymin)/2), distance))
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
                cv2.putText(frame, '{} {:.1%}'.format(det_label, detection.score),
                        (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 1)

            if draw_landmarks:
                for landmark in detection.landmarks:
                    cv2.circle(frame, landmark, 2, (0, 255, 255), 2)
    return frame, detected_objects, detected_boxes


# Functie folosita pentru a incarca modelul de recunoastere a obiectelor
def bypass_obj_det_args(args):
    args.architecture_type = 'ssd'
    args.device = 'MYRIAD'
    args.model = '/home/pi/Desktop/BionicaV2/models/faster_rcnn_resnet50_coco.xml'
    return args


# Functie folosita pentru a incarca modelul de recunoastere faciala
def bypass_face_det_args(args):
    args.architecture_type = 'faceboxes'
    args.device = 'MYRIAD'
    args.model = '/home/pi/Desktop/BionicaV2/models/faceboxes-pytorch.xml'
    return args


# Functia incarca pe NCS2 si configureaza modelele pentru recunoastere faciala si a obiectelor
def init_myriad():
    global o_args, log, ie, o_plugin_config, log, o_model, has_landmarks, o_detector_pipeline
    o_args = build_argparser().parse_args()
    o_args = bypass_obj_det_args(o_args)

    f_args = build_argparser().parse_args()
    f_args = bypass_face_det_args(f_args)
    
    log.info('Initializing Inference Engine...')
    ie = IECore()

    o_plugin_config = get_plugin_configs(o_args.device, o_args.num_streams, o_args.num_threads)

    log.info('Loading object detection network...')

    o_model = get_model(ie, o_args)
    o_model.labels = [
    '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
    'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign',
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A', 'N/A',
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'N/A', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
    'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
    'donut', 'cake', 'chair', 'couch', 'plant', 'bed', 'N/A', 'dining table',
    'N/A', 'N/A', 'toilet', 'N/A', 'TV', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book',
    'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
    ]

    log.info('Loading face detection network...')

    f_model = get_model(ie, f_args)
    f_model.labels  = ['face', 'background']
    
    has_landmarks = o_args.architecture_type == 'retina'

    o_detector_pipeline = AsyncPipeline(ie, o_model, o_plugin_config,
                                      device=o_args.device, max_num_requests=o_args.num_infer_requests)
    f_detector_pipeline = AsyncPipeline(ie, f_model, o_plugin_config,
                                      device=f_args.device, max_num_requests=f_args.num_infer_requests)
    return o_model, o_detector_pipeline, f_model, f_detector_pipeline

