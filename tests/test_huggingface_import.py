"""
Ensure that we can load huggingface/transformer GPTs into minGPT
"""

import unittest
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from mingpt.model import GPT
from mingpt.utils import sample

# -----------------------------------------------------------------------------

class TestHuggingFaceImport(unittest.TestCase):

    def test_gpt2(self):
        model_type = 'gpt2'
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        prompt = "Hello, my dog is a little"

        # create a minGPT and a huggingface/transformers model
        model = GPT.from_pretrained(model_type)
        model_hf = GPT2LMHeadModel.from_pretrained(model_type) # init a HF model too

        # ship both to device
        model.to(device)
        model_hf.to(device)
        # set both to eval mode
        model.eval()
        model_hf.eval()

        # tokenize an input prompt
        tokenizer = GPT2Tokenizer.from_pretrained(model_type)
        model_hf.config.pad_token_id = model_hf.config.eos_token_id # suppress a warning
        if prompt == '': # to create unconditional samples we feed in the special start token
            prompt = '<|endoftext|>'
        encoded_input = tokenizer(prompt, return_tensors='pt').to(device)
        x = encoded_input['input_ids']

        # ensure the logits match exactly
        logits1, loss = model(x)
        logits2 = model_hf(x).logits
        self.assertTrue(torch.allclose(logits1, logits2))

        # now draw the argmax samples from each and compare them
        y1 = sample(model=model, x=x, steps=20, sample=False)[0]
        out1 = tokenizer.decode(y1.cpu().squeeze())
        y2 = model_hf.generate(x, max_new_tokens=20, do_sample=False)[0]
        out2 = tokenizer.decode(y2.cpu().squeeze())
        self.assertTrue(torch.equal(y1, y2))
        self.assertTrue(out1 == out2) # compare the output strings too, exactly


if __name__ == '__main__':
    unittest.main()