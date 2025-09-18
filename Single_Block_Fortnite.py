import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class EmbeddingNN(nn.Module):
    def __init__(self, vocab_size, hidden_dim, max_sequence_length):
        super().__init__()

        self.fc1 = nn.Embedding(num_embeddings = vocab_size, embedding_dim = hidden_dim)
        self.pos_embedding = nn.Embedding(num_embeddings = max_sequence_length , embedding_dim = hidden_dim)

    def forward(self, X, pos):

        word_embedding = self.fc1(X)
        pos_embedding = self.pos_embedding(pos)
        #X = self.fc2(X)
        return word_embedding + pos_embedding

class AttentionNN(nn.Module):
    def __init__(self,hidden_dim, num_of_head):
        super().__init__()

        self.num_of_head = num_of_head
        self.head_dim = hidden_dim // num_of_head

        self.Q_m = nn.Linear(hidden_dim,hidden_dim)
        self.K_m = nn.Linear(hidden_dim,hidden_dim)
        self.V_m = nn.Linear(hidden_dim,hidden_dim)

        self.W_O = nn.Linear(hidden_dim,hidden_dim)


    def forward(self, X):

        batch_size , seq_len , hidden_dim = X.shape

        Q = self.Q_m(X)
        K = self.K_m(X)
        V = self.V_m(X)

        Q = Q.view(batch_size , seq_len , self.num_of_head , self.head_dim).transpose(1,2)
        K = K.view(batch_size , seq_len , self.num_of_head , self.head_dim).transpose(1,2)
        V = V.view(batch_size , seq_len , self.num_of_head , self.head_dim).transpose(1,2)

        scores = torch.matmul(Q , K.transpose(-2,-1))
        scaled_scores = scores / np.sqrt((hidden_dim / num_of_head))
        attention_weights = torch.softmax(scaled_scores, dim = -1)
        output = torch.matmul(attention_weights , V)
        output = output.transpose(1,2).contiguous().view(batch_size, seq_len, hidden_dim)
        output = self.W_O(output)
        
        return output

class NormNN(nn.Module):
    def __init__(self,hidden_dim):
        super().__init__()

        self.layer_norm = nn.LayerNorm(hidden_dim)

    def forward(self,x):

        x = self.layer_norm(x)

        return x

class FFN(nn.Module):
    def __init__(self,hidden_dim):
        super().__init__()

        

        self.ffn1 = nn.Linear(hidden_dim , (hidden_dim*4))
        self.gelu = nn.GELU()
        self.ffn2 = nn.Linear((hidden_dim*4) , hidden_dim)

    def forward(self,X):

        X = self.ffn1(X)
        X = self.gelu(X)
        X = self.ffn2(X)

        return X
        