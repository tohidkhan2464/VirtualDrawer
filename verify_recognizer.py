import sys
import os
import math
import time

# Add the project workspace to path so we can import src
sys.path.insert(0, os.path.abspath("."))

from src.gesture_recognizer import GestureRecognizer, Gesture

def make_mock_landmarks(finger_states, hand_type="Right", is_pinch=False):
    """
    Helper to construct a mock list of 21 landmarks [[idx, x, y], ...]
    based on the desired finger states.
    For reference:
    - 0: Wrist (0, 100)
    - 9: Middle MCP (0, 50) -> hand size = 50
    - Index MCP (6) is at (10, 40), Index Tip (8) is at (10, 20) if UP, (10, 45) if DOWN
    """
    landmarks = [[i, 0, 100] for i in range(21)]
    
    # Wrist (0) and Middle MCP (9) to establish hand_size = 100
    landmarks[0] = [0, 0, 100]
    landmarks[9] = [9, 0, 0] # y distance of 100
    
    # Finger tip and pip mapping
    tips = {"index": 8, "middle": 12, "ring": 16, "pinky": 20}
    pips = {"index": 6, "middle": 10, "ring": 14, "pinky": 18}
    
    for name in tips:
        tip_id = tips[name]
        pip_id = pips[name]
        if finger_states.get(name, False):
            # UP: tip y < pip y
            landmarks[pip_id] = [pip_id, 10, 40]
            landmarks[tip_id] = [tip_id, 10, 20]
        else:
            # DOWN: tip y >= pip y
            landmarks[pip_id] = [pip_id, 10, 40]
            landmarks[tip_id] = [tip_id, 10, 50]
            
    # Thumb setup (landmark 4 tip, landmark 2 joint, landmark 5 index MCP)
    landmarks[5] = [5, 20, 30] # index MCP
    
    if finger_states.get("thumb", False):
        # Standard thumb extension
        if hand_type == "Right":
            landmarks[2] = [2, 30, 40]
            landmarks[4] = [4, 60, 30] # tip_x = 60, joint_x = 30 -> 60 > 30 (UP)
        else:
            landmarks[2] = [2, 30, 40]
            landmarks[4] = [4, 10, 30] # tip_x = 10, joint_x = 30 -> 10 < 30 (UP)
    else:
        # Folded thumb (close to index MCP 5)
        landmarks[2] = [2, 30, 40]
        landmarks[4] = [4, 22, 32] # very close to index MCP (5), so thumb_index_mcp_dist < 0.35
        
    # Override for Pinch
    if is_pinch:
        # Thumb tip (4) and Index tip (8) are very close
        landmarks[4] = [4, 15, 20]
        landmarks[8] = [8, 15, 20]
            
    return landmarks

def test_gesture_recognition_v2():
    recognizer = GestureRecognizer()
    
    print("Running Gesture Set v2 recognition tests...\n")
    
    # ----------------------------------------------------
    # SINGLE HAND TESTS - RIGHT HAND (Dominant)
    # ----------------------------------------------------
    print("--- Right Hand (Dominant) Tests ---")
    # Test 1: Right Hand DRAW (Index UP, others DOWN)
    states_r = {"thumb": False, "index": True, "middle": False, "ring": False, "pinky": False}
    lms_r = make_mock_landmarks(states_r, "Right")
    hands = [{"hand_type": "Right", "landmarks": lms_r}]
    res = recognizer.recognize_hands(hands)
    print(f"Right DRAW: Expected = draw, Got = {res['right_gesture']}")
    assert res["right_gesture"] == Gesture.DRAW

    # Test 2: Right Hand SELECT (Index + Middle UP, others DOWN)
    states_r = {"thumb": False, "index": True, "middle": True, "ring": False, "pinky": False}
    lms_r = make_mock_landmarks(states_r, "Right")
    hands = [{"hand_type": "Right", "landmarks": lms_r}]
    res = recognizer.recognize_hands(hands)
    print(f"Right SELECT: Expected = select, Got = {res['right_gesture']}")
    assert res["right_gesture"] == Gesture.SELECT

    # Test 3: Right Hand PAUSE (All UP)
    states_r = {"thumb": True, "index": True, "middle": True, "ring": True, "pinky": True}
    lms_r = make_mock_landmarks(states_r, "Right")
    hands = [{"hand_type": "Right", "landmarks": lms_r}]
    res = recognizer.recognize_hands(hands)
    print(f"Right PAUSE: Expected = pause, Got = {res['right_gesture']}")
    assert res["right_gesture"] == Gesture.PAUSE

    # Test 4: Right Hand PINCH
    states_r = {"thumb": True, "index": True, "middle": False, "ring": False, "pinky": False}
    lms_r = make_mock_landmarks(states_r, "Right", is_pinch=True)
    hands = [{"hand_type": "Right", "landmarks": lms_r}]
    res = recognizer.recognize_hands(hands)
    print(f"Right PINCH: Expected = pinch, Got = {res['right_gesture']}")
    assert res["right_gesture"] == Gesture.PINCH

    # ----------------------------------------------------
    # SINGLE HAND TESTS - LEFT HAND (Modifier)
    # ----------------------------------------------------
    print("\n--- Left Hand (Modifier) Tests ---")
    # Test 5: Left Hand ERASE (Index, Middle, Ring UP)
    states_l = {"thumb": False, "index": True, "middle": True, "ring": True, "pinky": False}
    lms_l = make_mock_landmarks(states_l, "Left")
    hands = [{"hand_type": "Left", "landmarks": lms_l}]
    res = recognizer.recognize_hands(hands)
    print(f"Left ERASE: Expected = erase, Got = {res['left_gesture']}")
    assert res["left_gesture"] == Gesture.ERASE

    # Test 6: Left Hand TEXT_MODE (Index, Middle UP)
    states_l = {"thumb": False, "index": True, "middle": True, "ring": False, "pinky": False}
    lms_l = make_mock_landmarks(states_l, "Left")
    hands = [{"hand_type": "Left", "landmarks": lms_l}]
    res = recognizer.recognize_hands(hands)
    print(f"Left TEXT_MODE: Expected = text_mode, Got = {res['left_gesture']}")
    assert res["left_gesture"] == Gesture.TEXT_MODE

    # Test 7: Left Hand BRUSH_MENU (Thumb UP, others DOWN)
    states_l = {"thumb": True, "index": False, "middle": False, "ring": False, "pinky": False}
    lms_l = make_mock_landmarks(states_l, "Left")
    hands = [{"hand_type": "Left", "landmarks": lms_l}]
    res = recognizer.recognize_hands(hands)
    print(f"Left BRUSH_MENU: Expected = brush_menu, Got = {res['left_gesture']}")
    assert res["left_gesture"] == Gesture.BRUSH_MENU

    # Test 8: Left Hand COLOR_MENU (Pinky UP, others DOWN)
    states_l = {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": True}
    lms_l = make_mock_landmarks(states_l, "Left")
    hands = [{"hand_type": "Left", "landmarks": lms_l}]
    res = recognizer.recognize_hands(hands)
    print(f"Left COLOR_MENU: Expected = color_menu, Got = {res['left_gesture']}")
    assert res["left_gesture"] == Gesture.COLOR_MENU

    # ----------------------------------------------------
    # TWO-HAND TESTS
    # ----------------------------------------------------
    print("\n--- Two-Hand Combo Tests ---")
    
    # Test 9: SAVE (Right Thumb UP + Left Thumb UP) - Stateful hold
    st_r = {"thumb": True, "index": False, "middle": False, "ring": False, "pinky": False}
    st_l = {"thumb": True, "index": False, "middle": False, "ring": False, "pinky": False}
    lm_r = make_mock_landmarks(st_r, "Right")
    lm_l = make_mock_landmarks(st_l, "Left")
    hands = [{"hand_type": "Right", "landmarks": lm_r}, {"hand_type": "Left", "landmarks": lm_l}]
    
    res = recognizer.recognize_hands(hands)
    print(f"Save Initial: Expected = save_hold, Got = {res['global_gesture']}, Progress = {res['global_progress']:.2f}")
    assert res["global_gesture"] == Gesture.SAVE_HOLD
    
    recognizer.save_start_time = time.time() - 2.0
    res = recognizer.recognize_hands(hands)
    print(f"Save Triggered: Expected = save, Got = {res['global_gesture']}, Progress = {res['global_progress']:.2f}")
    assert res["global_gesture"] == Gesture.SAVE

    # Test 10: CLEAR CANVAS (Right Palm + Left Palm) - Stateful hold
    st_r = {"thumb": True, "index": True, "middle": True, "ring": True, "pinky": True}
    st_l = {"thumb": True, "index": True, "middle": True, "ring": True, "pinky": True}
    lm_r = make_mock_landmarks(st_r, "Right")
    lm_l = make_mock_landmarks(st_l, "Left")
    hands = [{"hand_type": "Right", "landmarks": lm_r}, {"hand_type": "Left", "landmarks": lm_l}]
    
    res = recognizer.recognize_hands(hands)
    print(f"Clear Initial: Expected = clear_hold, Got = {res['global_gesture']}, Progress = {res['global_progress']:.2f}")
    assert res["global_gesture"] == Gesture.CLEAR_HOLD
    
    recognizer.clear_canvas_start_time = time.time() - 3.0
    res = recognizer.recognize_hands(hands)
    print(f"Clear Triggered: Expected = clear_canvas, Got = {res['global_gesture']}, Progress = {res['global_progress']:.2f}")
    assert res["global_gesture"] == Gesture.CLEAR_CANVAS

    # Test 11: UNDO (Right Index UP + Left Index UP) - Stateful hold
    st_r = {"thumb": False, "index": True, "middle": False, "ring": False, "pinky": False}
    st_l = {"thumb": False, "index": True, "middle": False, "ring": False, "pinky": False}
    lm_r = make_mock_landmarks(st_r, "Right")
    lm_l = make_mock_landmarks(st_l, "Left")
    hands = [{"hand_type": "Right", "landmarks": lm_r}, {"hand_type": "Left", "landmarks": lm_l}]
    
    res = recognizer.recognize_hands(hands)
    print(f"Undo Initial: Expected = undo_hold, Got = {res['global_gesture']}, Progress = {res['global_progress']:.2f}")
    assert res["global_gesture"] == Gesture.UNDO_HOLD
    
    recognizer.undo_start_time = time.time() - 1.0
    res = recognizer.recognize_hands(hands)
    print(f"Undo Triggered: Expected = undo, Got = {res['global_gesture']}, Progress = {res['global_progress']:.2f}")
    assert res["global_gesture"] == Gesture.UNDO

    # Test 12: REDO (Right 2 Fingers + Left 2 Fingers)
    st_r = {"thumb": False, "index": True, "middle": True, "ring": False, "pinky": False}
    st_l = {"thumb": False, "index": True, "middle": True, "ring": False, "pinky": False}
    lm_r = make_mock_landmarks(st_r, "Right")
    lm_l = make_mock_landmarks(st_l, "Left")
    hands = [{"hand_type": "Right", "landmarks": lm_r}, {"hand_type": "Left", "landmarks": lm_l}]
    res = recognizer.recognize_hands(hands)
    print(f"Redo Triggered: Expected = redo, Got = {res['global_gesture']}")
    assert res["global_gesture"] == Gesture.REDO

    # Test 13: ZOOM (Right Pinch + Left Pinch)
    st_r = {"thumb": True, "index": True, "middle": False, "ring": False, "pinky": False}
    st_l = {"thumb": True, "index": True, "middle": False, "ring": False, "pinky": False}
    lm_r = make_mock_landmarks(st_r, "Right", is_pinch=True)
    lm_l = make_mock_landmarks(st_l, "Left", is_pinch=True)
    hands = [{"hand_type": "Right", "landmarks": lm_r}, {"hand_type": "Left", "landmarks": lm_l}]
    res = recognizer.recognize_hands(hands)
    print(f"Zoom Triggered: Expected = zoom, Got = {res['global_gesture']}")
    assert res["global_gesture"] == Gesture.ZOOM

    # Test 14: NEXT TOOL (Right 3 Fingers + Left 3 Fingers)
    st_r = {"thumb": False, "index": True, "middle": True, "ring": True, "pinky": False}
    st_l = {"thumb": False, "index": True, "middle": True, "ring": True, "pinky": False}
    lm_r = make_mock_landmarks(st_r, "Right")
    lm_l = make_mock_landmarks(st_l, "Left")
    hands = [{"hand_type": "Right", "landmarks": lm_r}, {"hand_type": "Left", "landmarks": lm_l}]
    res = recognizer.recognize_hands(hands)
    print(f"Next Tool Triggered: Expected = next_tool, Got = {res['global_gesture']}")
    assert res["global_gesture"] == Gesture.NEXT_TOOL
    
    print("\nAll Gesture Set v2 tests passed successfully!")

if __name__ == "__main__":
    test_gesture_recognition_v2()
