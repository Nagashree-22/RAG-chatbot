import sys
import unittest

import api
from models.emotion import detect_emotion
from models.rag import retrieve_documents


class MindCareTests(unittest.TestCase):
    def test_application_does_not_load_transformers(self):
        self.assertNotIn("transformers", sys.modules)

    def test_emotion_detection_handles_punctuation(self):
        self.assertEqual(detect_emotion("I feel happy and excited!")["emotion"], "joy")

    def test_health_input_selects_caring_robot(self):
        emotion = detect_emotion("I have a fever today")["emotion"]
        self.assertEqual(api.ROBOT_IMAGES[emotion], "robot_caring.png")

    def test_emotion_robot_mapping(self):
        self.assertEqual(api.ROBOT_IMAGES["joy"], "robot_happy.png")
        self.assertEqual(api.ROBOT_IMAGES["sadness"], "robot_sad.png")
        self.assertEqual(api.ROBOT_IMAGES["anger"], "robot_angry.png")
        self.assertEqual(api.ROBOT_IMAGES["fear"], "robot_fear.png")

    def test_emotion_preview_matches_user_input(self):
        preview = api._emotion_payload("I am happy!")
        self.assertEqual(preview["emotion"], "joy")
        self.assertEqual(preview["robot_image"], "/assets/robot_happy.png")
        self.assertTrue(preview["suggestions"])

    def test_chat_prompt_includes_recent_turns_and_forward_looking_support(self):
        conversation = [
            api.ChatTurn(role="user", content="I am nervous about my exam."),
            api.ChatTurn(role="assistant", content="That sounds stressful."),
        ]

        messages = api._chat_messages(
            "I studied for twenty minutes.",
            "Study support context",
            conversation,
        )

        self.assertEqual([message["role"] for message in messages], [
            "system",
            "user",
            "assistant",
            "user",
        ])
        self.assertIn("one small, realistic next step", messages[0]["content"])
        self.assertEqual(messages[1]["content"], "I am nervous about my exam.")
        self.assertEqual(messages[-1]["content"], (
            "Relevant context:\nStudy support context\n\n"
            "User message: I studied for twenty minutes."
        ))

    def test_knowledge_base_retrieves_documents(self):
        self.assertTrue(retrieve_documents("How can I manage anxiety?"))


if __name__ == "__main__":
    unittest.main()
