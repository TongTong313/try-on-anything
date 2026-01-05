from try_on_anything.pipelines import AccessoryTryOnPipeline
import logging
import asyncio

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


if __name__ == "__main__":
    # 示例用法
    pipeline = AccessoryTryOnPipeline(use_vl_model=True)

    # 使用 asyncio.run() 调用异步的 run 方法
    result = asyncio.run(pipeline.run(
        accessory_img_path="./tests/imgs/w1.png",
        person_img_path="./tests/imgs/h1.jpg",
        vl_model_name="qwen3-vl-plus",
        img_gen_model_name="wan2.6-image"
    ))

    print(result)
