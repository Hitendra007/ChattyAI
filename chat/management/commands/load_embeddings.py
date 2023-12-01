# chatty-main/chat/management/commands/load_embeddings.py

import os
from django.core.management.base import BaseCommand

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.document_loaders import TextLoader
import pinecone


class Command(BaseCommand):
    help = 'Load embeddings into Pinecone from FAQ.txt.'

    def handle(self, *args, **kwargs):
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

        # initialize pinecone
        pinecone.init(
            api_key=os.environ.get("PINECONE_API_KEY"),
            environment=os.environ.get("PINECONE_ENV"),
        )
        index_name = os.environ.get("PINECONE_INDEX_NAME")
        index = pinecone.Index(index_name=index_name)

        index.delete(delete_all=True)
        loader = TextLoader(r"chat/FAQ.txt", encoding='utf-8')
        documents = loader.load()

        text_splitter = CharacterTextSplitter(
            separator="question",
            chunk_size=300,
            chunk_overlap=20,
            length_function=len,
        )

        docs = text_splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings()

        Pinecone.from_documents(docs, embeddings, index_name=index_name)

        self.stdout.write(self.style.SUCCESS('Successfully Loaded Embeddings Into Pinecone.'))
