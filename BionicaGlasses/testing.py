from picamera.array import PiRGBArray
from picamera import PiCamera
from object_detection_demo import *
import cv2

def process_image(input_image, display=True):
    global next_frame_id, next_frame_id_to_show, detector_pipeline
    
    while True:
        if detector_pipeline.callback_exceptions:
            raise detector_pipeline.callback_exceptions[0]
        
        results = detector_pipeline.get_result(next_frame_id_to_show)
        if results:
            print(f"[ INFO ] Image with ID {next_frame_id_to_show} received")
            objects, frame_meta = results
            frame = frame_meta['frame']
            frame, detected_objects = draw_detections(frame, objects, palette, model.labels, 0.6, False)
            
            if display:
                cv2.imshow(f"Result {next_frame_id_to_show}", frame)
                key = cv2.waitKey(0)
                cv2.destroyAllWindows()
            next_frame_id_to_show += 1
            break
            
        if detector_pipeline.is_ready():
            print(f"[ INFO ] Image with ID {next_frame_id} sent to pipeline")
            detector_pipeline.submit_data(input_image, next_frame_id, {'frame': input_image, 'start_time': 0})
            next_frame_id += 1
        else:
            print("[ INFO ] Pipeline await any")
            detector_pipeline.await_any()
    return frame, detected_objects
        
def take_picture():
    global camera, rawCapture
    camera.capture(rawCapture, format="bgr")
    image = rawCapture.array
    image = cv2.rotate(image, cv2.ROTATE_180)
    rawCapture.truncate(0)
    return image
    
def take_video():
    global camera, rawCapture, next_frame_id_to_show
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port="True"):
        image = frame.array
        rawCapture.truncate(0)
        image = cv2.rotate(image, cv2.ROTATE_180)
        image, detected_objects = process_image(image, display=False)
        cv2.imshow("Video", image)
        key = cv2.waitKey(1)
        
        if key in {ord('q'), ord('Q')}:
            break
    cv2.destroyAllWindows()
    
def main():
    global camera, rawCapture, model, detector_pipeline, palette, next_frame_id, next_frame_id_to_show
    camera = PiCamera()
    camera.resolution = (1024,608)
    camera.framerate = 1
    rawCapture = PiRGBArray(camera)
    model, detector_pipeline = init_myriad()
    palette = ColorPalette(len(model.labels) if model.labels else 100)
    next_frame_id = 0
    next_frame_id_to_show = 0
    
    #for i in range(5):
    #    image = take_picture()
    #    _, detected_objects = process_image(image)
    #    print(detected_objects)
    take_video()    

if __name__ == '__main__':
    main()


