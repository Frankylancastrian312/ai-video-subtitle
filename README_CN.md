# ai-video-subtitle

[English](./README.md) | [简体中文](./README_CN.md)

把视频变成翻译好、切分对齐的字幕——需要的话再配上配音——**只用一个 API 密钥**。

转录、断句、术语提取、翻译和配音全部走 [dlazy](https://dlazy.com) API。不用下载
本地模型，不用准备 GPU，也不用同时管理一堆各家厂商的密钥。

## 它做什么

丢进一个视频文件或 YouTube 链接，流水线依次跑：

1. **逐词转录**——dlazy 语音识别，带每个词的时间戳
2. **断句**——spaCy 负责结构，LLM 负责语义
3. **摘要与术语提取**——先建术语表，让人名和专有名词在整支视频里保持一致
4. **多步反思式翻译**——翻译、自我批评、修订
5. **字幕切分与对齐**——按词级时间戳拆长句，避免时间轴漂移
6. **压制**（可选）——把字幕烧进视频
7. **配音**（可选）——逐句 TTS，按字幕时间轴调速，再合回视频

## 环境要求

- Python 3.10
- PATH 里有 ffmpeg
- 一个 dlazy API 密钥——在
  [dlazy.com/dashboard/organization/api-key](https://dlazy.com/dashboard/organization/api-key) 获取

## 安装

### 方式 A —— uv（不需要 Anaconda）

```bash
git clone https://github.com/dlazyai/ai-video-subtitle.git
cd ai-video-subtitle
python setup_env.py
```

Windows 下用 `OneKeyStart_uv.bat` 启动，或者：

```bash
.venv/bin/streamlit run st.py
```

### 方式 B —— conda

```bash
git clone https://github.com/dlazyai/ai-video-subtitle.git
cd ai-video-subtitle
conda create -n ai-video-subtitle python=3.10 -y
conda activate ai-video-subtitle
python install.py
streamlit run st.py
```

### 方式 C —— Docker

```bash
docker build -t ai-video-subtitle .
docker run -p 8501:8501 ai-video-subtitle
```

镜像基于 `python:3.10-slim`——不带 CUDA 基础层，因为没有任何东西在本地跑。

## 配置

打开侧边栏，把 dlazy API 密钥粘进去，配置就结束了。下面的模型选择器是从你的账号
实时拉取的，所以只会列出你的密钥真正能跑的模型：

| 设置项 | 可选 |
| --- | --- |
| 大语言模型 | `claude-sonnet-5`、`qwen3.8-max`、`kimi-k3` |
| 语音识别模型 | `fun-asr`、`elevenlabs-stt` |
| 配音模型 | `qwen-tts`、`doubao-tts`、`elevenlabs-tts` |
| 音色 | 从所选配音模型的音色表加载 |

其余参数都在 `config.yaml` 里，设置页会替你写入。

## 批量模式

需要无人值守批量处理时，见 [batch/README.zh.md](batch/README.zh.md)。

## 已知限制

把所有模型收敛到一家之后，这个 fork 确实放弃了一些东西，如实列在这里：

- **源语言只支持英文和中文。** dlazy 的语音识别工具只接受 `zh` 或 `en`。
  *目标*翻译语言不受限制，用自然语言描述即可，LLM 能理解。
- **没有人声分离。** 背景音乐很响的视频，转录准确率会低于上游开 Demucs 的效果。
- **没有音色克隆。** 配音只能用预置音色。

## 致谢

基于 [VideoLingo](https://github.com/Huanshere/VideoLingo)（作者 Huanyu，
Apache-2.0 许可）构建。流水线设计出自上游，本 fork 只是把模型层换成了 dlazy。
完整改动清单见 [NOTICE.md](NOTICE.md)。

## 许可证

Apache-2.0——见 [LICENSE](LICENSE)。
