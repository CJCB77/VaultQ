"""
Tests for the RAG workflow
"""
from unittest.mock import patch, MagicMock, ANY
from django.test import TestCase
from chat.rag import run_rag_and_llm


@patch("chat.rag.create_retrieval_chain")
@patch("chat.rag.create_history_aware_retriever")
class RagUnitTests(TestCase):
    """
    Class to test RAG functionality when querying chat
    """
    def setUp(self):
        # a minimal history: one system message + one prior user turn
        self.history = [
            {"role": "system","content": "You are a helpful assistant."},
        ]
        self.collection_name = "proj_1234_1680000000"
        self.query =  {"role": "user","content": "What is AI?"}


    def test_rag_builds_and_invokes_chain(self, mock_hist_retr, mock_create_chain):
        # Stub out the history-aware retriever
        """
        Test that the RAG workflow builds a history-aware retriever and a conversational retrieval chain,
        and then uses the chain to answer the user's question.

        The test verifies:

        - that the history-aware retriever was constructed with the last user question
        - that the retrieval chain was built from that retriever and a docs-combiner
        - that the chain was invoked with the correct parameters
        - that the answer returned was exactly what the chain returned
        """
        dummy_retriever = MagicMock(name="HistoryAwareRetriever")
        mock_hist_retr.return_value = dummy_retriever

        # Stub out the final QA chain and its invoke
        dummy_chain = MagicMock(name="RetrievalChain")
        dummy_chain.invoke.return_value = {"text":"AI is..."}
        mock_create_chain.return_value = dummy_chain

        # Now import and call the helper under test
        answer = run_rag_and_llm(self.collection_name, self.history, self.query)
        
        # It should return exactly what dummy_chain.invoke returned
        self.assertEqual(answer, "AI is...")

        # Verify we constructed the history_aware_retriever with the last user question
        # We dont know which LLM we passed so ANY is fine
        mock_hist_retr.assert_called_once_with(
            ANY, # LLM instance
            ANY, # Retriever
            ANY  # Prompt contextualization
        )
        # Verify we built the retrieval chain from that retriever and a docs-combiner
        mock_create_chain.assert_called_once_with(
            dummy_retriever, # the patched retriever
            ANY # the chain we passed in
        )

        # Finally assert that invoke() was called with exactly what our helper func does:
        dummy_chain.invoke.assert_called_once_with(
            "input": self.query,
            "chat_history": self.history,
        )

    def test_error_handling(self):
        """Test RAG failure scenarios"""
        with patch("chat.rag.create_history_aware_retriever") as mock_retriever:
            mock_retriever.side_effect = Exception("Vector store unavailable")
            
            with self.assertRaises(Exception) as context:
                run_rag_and_llm(
                    collection_name=self.collection_name,
                    chat_history=self.history,
                    query=self.query
                )
            
            self.assertIn("Vector store unavailable", str(context.exception))
    
    def test_source_document_handling(self):
        """Test proper extraction of source metadata"""
        with patch("chat.rag.create_retrieval_chain") as mock_chain:
            mock_chain.return_value.invoke.return_value = {
                "answer": "Test",
                "source_documents": [
                    MagicMock(metadata={"source": "doc1.pdf"}),
                    MagicMock(metadata={"source": "doc2.pdf"})
                ]
            }
            
            result = run_rag_and_llm(...)
            self.assertEqual(result["sources"], ["doc1.pdf", "doc2.pdf"])