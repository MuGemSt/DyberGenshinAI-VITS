# coding:utf-8
import os
import sys

if sys.platform == "darwin":
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import logging

logging.getLogger("numba").setLevel(logging.WARNING)
logging.getLogger("markdown_it").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO, format="| %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

import torch
from tqdm import tqdm
from .models import SynthesizerTrn
from .text.symbols import symbols
from .utils import (
    text_splitter,
    concatenate_audios,
    get_text,
    download_file,
    get_hparams_from_url,
    load_checkpoint,
    save_audio,
)
from modelscope import snapshot_download


class TTS:
    def __init__(self):
        domain = "https://www.modelscope.cn/api/v1/models/MuGemSt/Hoyo-Bert-VITS2-V1/repo?Revision=master&FilePath="
        model_path = download_file(domain + "G_78000.pth")
        self.hps = get_hparams_from_url(domain + "config.json")
        self.device = (
            "cuda:0"
            if torch.cuda.is_available()
            else (
                "mps"
                if sys.platform == "darwin" and torch.backends.mps.is_available()
                else "cpu"
            )
        )
        # 语言模型下载
        self.model_dir = snapshot_download("dienstag/chinese-roberta-wwm-ext-large")
        self.net_g = SynthesizerTrn(
            len(symbols),
            self.hps.data.filter_length // 2 + 1,
            self.hps.train.segment_size // self.hps.data.hop_length,
            n_speakers=self.hps.data.n_speakers,
            **self.hps.model,
        ).to(self.device)
        self.net_g.eval()
        load_checkpoint(model_path, self.net_g, None, skip_optimizer=True)
        self.stopping = False

    def _infer(self, text, sdp_ratio, noise_scale, noise_scale_w, length_scale, sid):
        bert, phones, tones, lang_ids = get_text(text, "ZH", self.hps, self.model_dir)
        with torch.no_grad():
            x_tst = phones.to(self.device).unsqueeze(0)
            tones = tones.to(self.device).unsqueeze(0)
            lang_ids = lang_ids.to(self.device).unsqueeze(0)
            bert = bert.to(self.device).unsqueeze(0)
            x_tst_lengths = torch.LongTensor([phones.size(0)]).to(self.device)
            del phones
            speakers = torch.LongTensor([self.hps.data.spk2id[sid]]).to(self.device)
            audio = (
                self.net_g.infer(
                    x_tst,
                    x_tst_lengths,
                    speakers,
                    tones,
                    lang_ids,
                    bert,
                    sdp_ratio=sdp_ratio,
                    noise_scale=noise_scale,
                    noise_scale_w=noise_scale_w,
                    length_scale=length_scale,
                )[0][0, 0]
                .data.cpu()
                .float()
                .numpy()
            )
            del x_tst, tones, lang_ids, bert, x_tst_lengths, speakers

            return audio

    def _tts_fn(
        self, text, speaker, sdp_ratio, noise_scale, noise_scale_w, length_scale
    ):
        with torch.no_grad():
            audio = self._infer(
                text,
                sdp_ratio=sdp_ratio,
                noise_scale=noise_scale,
                noise_scale_w=noise_scale_w,
                length_scale=length_scale,
                sid=speaker,
            )

        return (self.hps.data.sampling_rate, audio)

    def speech(
        self,
        content,
        speaker,
        sdp_ratio=0.2,
        noise_scale=0.6,
        noise_scale_w=0.8,
        length_scale=1,
    ):
        sentences = text_splitter(content)
        audios = []
        for sentence in tqdm(sentences, desc="TTS inferring..."):
            if self.stopping:
                return "", 0

            with torch.no_grad():
                audios.append(
                    self._infer(
                        sentence,
                        sdp_ratio=sdp_ratio,
                        noise_scale=noise_scale,
                        noise_scale_w=noise_scale_w,
                        length_scale=length_scale,
                        sid=speaker,
                    )
                )

        if self.stopping:
            return "", 0

        sr, audio_samples = concatenate_audios(audios, self.hps.data.sampling_rate)

        if self.stopping:
            return "", 0

        return save_audio(audio_samples, sr)
