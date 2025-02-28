from typing import List

import numpy as np
import onnxruntime
import os

from espnet_onnx.utils.config import Config

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OMP_WAIT_POLICY"] = "PASSIVE"

class JETS:
    def __init__(
        self,
        config: Config,
        providers: List[str],
        use_quantized: bool = False,
    ):
        self.config = config
        opts = onnxruntime.SessionOptions()
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1
        opts.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
        if use_quantized:
            self.model = onnxruntime.InferenceSession(
                self.config.quantized_model_path,
                providers=providers, sess_options=opts
            )
        else:
            self.model = onnxruntime.InferenceSession(
                self.config.model_path,
                providers=providers, sess_options=opts
            )

        self.input_names = [d.name for d in self.model.get_inputs()]
        self.use_sids = "sids" in self.input_names
        self.use_lids = "lids" in self.input_names
        self.use_feats = "feats" in self.input_names
        self.use_spk_embed_dim = "spembs" in self.input_names

    def __call__(
        self,
        text: np.ndarray,
        sids: np.ndarray = None,
        spembs: np.ndarray = None,
        lids: np.ndarray = None,
    ):
        output_names = ["wav", "dur"]
        input_dict = self.get_input_dict(text, sids, spembs, lids)
        wav, dur = self.model.run(output_names, input_dict)
        return dict(wav=wav, dur=dur)

    def get_input_dict(self, text, sids, spembs, lids):
        ret = {"text": text}
        ret = self._set_input_dict(ret, "sids", sids)
        ret = self._set_input_dict(ret, "spembs", spembs)
        ret = self._set_input_dict(ret, "lids", lids)
        return ret

    def _set_input_dict(self, dic, key, value):
        if key in self.input_names:
            assert value is not None
            dic[key] = value
        return dic
