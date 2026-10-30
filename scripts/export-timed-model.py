"""Add the encoder's per-phoneme frame durations to Kokoro as a `duration` output.

kokoro-onnx reports phoneme timings when the model has that output, which gives
word-level caption timing without a transcription model.
"""
import sys
import onnx

src, dst = sys.argv[1], sys.argv[2]
model = onnx.load(src)
model.graph.output.append(
    onnx.helper.make_tensor_value_info("duration", onnx.TensorProto.INT64, None)
)
# Clip output is float in some exports: cast to int64 under the name "duration"
model.graph.node.append(
    onnx.helper.make_node("Cast", ["/encoder/Clip_output_0"], ["duration"], to=onnx.TensorProto.INT64)
)
onnx.save(model, dst)
print("saved", dst)
