# Changelog

This document records all notable changes to this project.

## v1.1.0 - 2026-01-08

Building on v1.0.0, this version adds clothing try-on functionality and refactors the code architecture.

### New Features

#### Clothing Try-On Functionality
- Added `ClothingTryOnPipeline` for virtual try-on of various clothing items including tops, pants, skirts, jackets, etc.
- Added `ClothingTryOnImageGenerator` for clothing try-on image generation
- Added clothing try-on API endpoints (`/api/clothing-try-on/*`)
- Added clothing try-on service layer (`clothing_try_on_service`)
- Support for automatic clothing type and wearing position detection
- Support for manual specification of clothing type and wearing position to override VL model detection results

#### Code Architecture Optimization
- Added `common` module for unified type definitions and constants management
  - `common/types.py`: Defines `VLModelAccessoryParsedResult` and `VLModelClothingParsedResult` data models
  - `common/constants.py`: Unified management of WAN model, VL model, and image generation related constants
- Added `utils/image_utils.py` image processing utility module
- Renamed original `tryon` module to `accessory_try_on` for clearer naming
- Removed `pipelines/types.py`, migrated type definitions to `common/types.py`

#### API Route Adjustments
- Split original `/api/tryon/*` endpoints into two independent route groups:
  - `/api/accessory-try-on/*`: Accessory try-on related endpoints
  - `/api/clothing-try-on/*`: Clothing try-on related endpoints
- Frontend API calls split into `accessory-try-on.js` and `clothing-try-on.js` accordingly

#### Frontend Interface Updates
- Updated `TryOnView.vue` main view to support switching between accessory try-on and clothing try-on
- Updated `TaskSidebar.vue` task sidebar with optimized task display
- Updated internationalization files (Chinese and English) with clothing try-on related text
- Updated interface preview screenshots (`webview_zh.png` and `webview_en.png`)
- Optimized `ResultDisplay.vue` result display page layout to highlight result image (size increased from 300px to 600px), with original images displayed as thumbnails (150px), improving user experience

### Improvements

#### Core Module Optimization
- Optimized `QwenVLClient` vision-language model client for improved recognition accuracy
- Optimized `WanModelClient` image generation model client with improved error handling
- Optimized `BaseTryOnPipeline` base pipeline by extracting common logic
- Optimized `task_manager.py` task manager to support multiple task types (accessory try-on, clothing try-on)

#### Code Quality Improvements
- Unified constants management to avoid magic numbers
- Improved type definitions for enhanced code maintainability
- Optimized module structure for better code reusability

### Bug Fixes
- Fixed potential issues with task type determination in task manager
- Fixed edge case handling in image size calculations
- Fixed issue where clothing type and wearing position options in settings page still displayed Chinese text in English mode
- Fixed issue where wearing position tags (e.g., "Full Body") in result display page were not properly translated in English mode

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
