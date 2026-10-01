Put your exported YOLOv8 model here as `best.onnx`.

From your training folder:

    yolo export model=runs/detect/train/weights/best.pt format=onnx imgsz=640 opset=12 simplify=True

Class names are read from the ONNX metadata automatically, so labels like
`freshapples`, `rotten_banana` or `Rotten Oranges` all work.
