# Code adapted from https://github.com/IST-DASLab/sparsegpt/blob/master/datautils.py
#data.py
import numpy as np
import random
import torch
from datasets import load_dataset
from torch.utils.data import TensorDataset

# Set seed for reproducibility
def set_seed(seed):
    np.random.seed(seed)
    torch.random.manual_seed(seed)

# Wrapper for tokenized input IDs
class TokenizerWrapper:
    def __init__(self, input_ids):
        self.input_ids = input_ids

# Load and process wikitext2 dataset
def get_wikitext2(nsamples, seed, seqlen, tokenizer):
    # Load train and test datasets
    # cache_dir = "/tmp/hf_datasets_wikitext2_cache"
    traindata = load_dataset(path="Salesforce/wikitext", name="wikitext-2-raw-v1", split='train')
    testdata = load_dataset(path="Salesforce/wikitext", name="wikitext-2-raw-v1", split='test')

    # Use max_length from tokenizer or fallback to seqlen
    max_length = getattr(tokenizer, 'model_max_length', seqlen)

    # Encode datasets in manageable chunks
    train_text = " ".join(traindata['text'])
    trainenc = tokenizer(train_text, return_tensors='pt', max_length=max_length, truncation=True)
    test_text = "\n\n".join(testdata['text'])
    testenc = tokenizer(test_text, return_tensors='pt', max_length=max_length, truncation=True)

    # Generate samples from training set
    random.seed(seed)
    trainloader = []
    for _ in range(nsamples):
        i = random.randint(0, trainenc.input_ids.shape[1] - seqlen - 1)
        j = i + seqlen
        inp = trainenc.input_ids[:, i:j]
        attention_mask = trainenc.attention_mask[:, i:j] # Keep the corresponding mask slice
        tar = inp.clone()
        # tar[:, :-1] = -100
        trainloader.append((inp, attention_mask, tar))
    return trainloader, testenc

# Load and process c4 dataset
def get_c4(nsamples, seed, seqlen, tokenizer):
    # Load train and validation datasets
    traindata = load_dataset('allenai/c4', data_files={'train': 'en/c4-train.00000-of-01024.json.gz'}, split='train', verification_mode='no_checks')
    valdata = load_dataset('allenai/c4', data_files={'validation': 'en/c4-validation.00000-of-00008.json.gz'}, split='validation', verification_mode='no_checks')

    # Use max_length from tokenizer or fallback to seqlen
    max_length = getattr(tokenizer, 'model_max_length', seqlen)

    # Generate samples from training set
    random.seed(seed)
    trainloader = []
    for _ in range(nsamples):
        while True:
            i = random.randint(0, len(traindata) - 1)
            trainenc = tokenizer(traindata[i]['text'], return_tensors='pt', max_length=max_length, truncation=True)
            if trainenc.input_ids.shape[1] > seqlen:
                break
        i = random.randint(0, trainenc.input_ids.shape[1] - seqlen - 1)
        j = i + seqlen
        inp = trainenc.input_ids[:, i:j]
        attention_mask = trainenc.attention_mask[:, i:j] # Keep the corresponding mask slice
        tar = inp.clone()
        # tar[:, :-1] = -100
        trainloader.append((inp, attention_mask, tar))

    # Prepare validation dataset
    val_text = ' '.join(valdata[:1100]['text'])
    valenc = tokenizer(val_text, return_tensors='pt', max_length=max_length, truncation=True)
    valenc = valenc.input_ids[:, :(256 * seqlen)]
    valenc = TokenizerWrapper(valenc)
    # return trainloader, valenc, data
    return trainloader, valenc

# Function to select the appropriate loader based on dataset name
def get_loaders(name, nsamples=128, seed=0, seqlen=2048, tokenizer=None):
    if 'wikitext2' in name:
        return get_wikitext2(nsamples, seed, seqlen, tokenizer)
    if "c4" in name:
        return get_c4(nsamples, seed, seqlen, tokenizer)