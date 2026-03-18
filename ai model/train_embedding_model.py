from embedding_pipeline import trainAndSaveModel


if __name__ == "__main__":
    trainAndSaveModel(epochs=25, batchSize=32)
