# Changelog

This document records all notable changes to this project.

## v1.0.0 - 2026-01-04

Initial release implementing core accessory virtual try-on functionality based on VL model + image generation model.

### New Features

#### Core Try-On Pipeline
- Implemented `AccessoryTryOnPipeline` for virtual try-on of various accessories including necklaces, earrings, bracelets, watches, etc.
- Support for automatic accessory type and wearing position detection
- Support for automatic accessory detail region extraction and cropping to enhance try-on effects for small accessories
- Support for manual specification of accessory type and wearing position to override VL model detection results

#### Model Clients
- Implemented `QwenVLClient` for Qwen Vision-Language model
  - OpenAI-compatible API format support
  - Streaming output support
  - Thinking mode with configurable thinking budget
  - Currently supported models:
    - qwen3-vl-plus
    - qwen3-vl-flash (cheaper!)
- Implemented `WanModelClient` for Tongyi Wanxiang image generation model
  - Async request and task result polling support
  - Automatic Base64 encoding for local images
  - Support for both URL and local file path image inputs
  - Currently only supports wan2.6-image model

#### Image Generators
- Implemented `TryOnImageGenerator` for try-on effect image generation
  - Automatic optimal output size selection based on person image
  - Support for 8 common aspect ratios (1:1, 2:3, 3:2, 3:4, 4:3, 9:16, 16:9, 21:9)
  - Configurable negative prompts, prompt extension, and watermark options
- Implemented `DashScopeImageGenerator` base image generator
  - Encapsulated DashScope API async call logic
  - Automatic download of generated results to local storage

#### Project Infrastructure
- Using `uv` as package manager
- Configured `pyproject.toml` project metadata
- Added test scripts and example code

### Bug Fixes
No bug fixes in initial release.
