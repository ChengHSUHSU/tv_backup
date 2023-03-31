


from transformers import AutoTokenizer, AutoModel





class ContentEmbedding:
    def __init__(self, dataset, rs_config):
        # init model
        self.model = AutoModel.from_pretrained(\
                    rs_config['model']['bert_model_name'])

        # tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(\
                    rs_config['model']['bert_model_name'])
        

    def build_item_embedding(self, content):
        inputs = self.tokenizer(content, return_tensors="pt")
        outputs = self.model(**inputs)
        return outputs

    
