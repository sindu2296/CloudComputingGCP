import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import transformers
from transformers import AutoModel, BertTokenizerFast

# import BERT-base pretrained model
bert = AutoModel.from_pretrained('bert-base-uncased')

# Load the BERT tokenizer
tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased')
max_seq_len = 15
device = torch.device("cpu")

path = "application/static/bert/bert_model.pt"


class BERT_Arch(nn.Module):

    def __init__(self, bert):
      
      super(BERT_Arch, self).__init__()

      self.bert = bert 
      
      # dropout layer
      self.dropout = nn.Dropout(0.1)
      
      # relu activation function
      self.relu =  nn.ReLU()

      # dense layer 1
      self.fc1 = nn.Linear(768,512)
      
      # dense layer 2 (Output layer)
      self.fc2 = nn.Linear(512,3)

      #softmax activation function
      self.softmax = nn.LogSoftmax(dim=1)

    #define the forward pass
    def forward(self, sent_id, mask):

      #pass the inputs to the model  
      _, cls_hs = self.bert(sent_id, attention_mask=mask)
      
      x = self.fc1(cls_hs)

      x = self.relu(x)

      x = self.dropout(x)

      # output layer
      x = self.fc2(x)
      
      # apply softmax activation
      x = self.softmax(x)

      return x

model = BERT_Arch(bert)
model = model.load_state_dict(torch.load(path,map_location='cpu'))
# pass the pre-trained BERT to our define architecture

def predict_reject(messages):
  sent_id = tokenizer.batch_encode_plus(messages, padding=True, return_token_type_ids=False)
  new_text_test = tokenizer.batch_encode_plus(
    messages,
    max_length = max_seq_len,
    pad_to_max_length=True,
    truncation=True,
    return_token_type_ids=False
)
  # for test set
  new_test_seq = torch.tensor(new_text_test['input_ids'])
  new_test_mask = torch.tensor(new_text_test['attention_mask'])
  # get predictions for test data
  with torch.no_grad():
    preds = model(new_test_seq.to(device), new_test_mask.to(device))
    preds = preds.detach().cpu().numpy()
  # print the model's output
  preds = np.argmax(preds, axis = 1)
  print(preds)
  return preds