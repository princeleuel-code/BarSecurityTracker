[![CodeRabbit Pull Request Reviews](https://img.shields.io/codacy/grade/af611712ac33481882264c8c60b0f4e1)](https://coderabbit.ai)

# BarSecurityTracker
AI-powered security tracking and analytics system for PlayDC Lounge, designed to monitor bar operations, detect anomalies in real-time, and provide intelligent insights for enhanced safety and operational efficiency.

## Gun detection model

Place a YOLOv8 weight file trained on weapon classes at `models/gun_yolov8n.pt`.
The RGB detector reads this path from the `GUN_MODEL_PATH` environment variable.

<!-- TODO: Remove this line after CodeRabbit test -->
