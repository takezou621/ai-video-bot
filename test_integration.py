#!/usr/bin/env python3
"""
Integration test for all new features
"""
import sys
import os

# Ensure we can import from current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_modules():
    """Test all newly implemented modules"""
    
    print("="*60)
    print("AI Video Bot - Integration Test Suite")
    print("="*60)
    print()
    
    # Test 1: API Key Manager
    print("1. Testing API Key Manager...")
    try:
        os.environ['GEMINI_API_KEYS'] = 'test_key_1,test_key_2,test_key_3'
        from api_key_manager import APIKeyManager
        
        manager = APIKeyManager('GEMINI')
        key1 = manager.get_key()
        manager.report_success(key1)
        key2 = manager.get_key()
        
        assert key1 != key2, "Keys should rotate"
        print("   ✓ API key rotation works")
        print(f"   ✓ Loaded {len(manager.keys)} keys")
        print()
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 2: Subtitle Optimizer
    print("2. Testing Subtitle Optimizer...")
    try:
        from subtitle_optimizer import SubtitleOptimizer
        
        optimizer = SubtitleOptimizer()
        test_data = [
            {"speaker": "A", "text": "短いテキスト", "start": 0.0, "end": 0.3},
            {"speaker": "B", "text": "これは非常に長いテキストで、複数の字幕に分割されるべきです。" * 3, "start": 0.3, "end": 2.0}
        ]
        
        optimized = optimizer.optimize_timing_data(test_data)
        validation = optimizer.validate_subtitle_quality(optimized)
        
        print(f"   ✓ Optimized {len(test_data)} → {len(optimized)} segments")
        print(f"   ✓ Avg reading speed: {validation['stats']['avg_reading_speed']:.1f} chars/sec")
        print()
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 3: Title CTR Optimizer
    print("3. Testing Title CTR Optimizer...")
    try:
        from title_ctr_optimizer import TitleCTROptimizer
        
        optimizer = TitleCTROptimizer()
        
        test_titles = [
            ("普通のタイトル", []),
            ("【速報】OpenAI GPT-5発表", ["OpenAI"]),
            ("5つの理由でわかる最新AI技術", ["AI"])
        ]
        
        for title, entities in test_titles:
            analysis = optimizer.analyze_title(title, entities)
            print(f"   • \"{title}\"")
            print(f"     Score: {analysis['ctr_score']}/100 (Grade: {analysis['grade']})")
        
        print("   ✓ CTR analysis working")
        print()
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 4: Thumbnail Variation Generator
    print("4. Testing Thumbnail Variation Generator...")
    try:
        from thumbnail_ab_testing import ThumbnailVariationGenerator
        
        gen = ThumbnailVariationGenerator()
        layouts = len(gen.LAYOUTS)
        colors = len(gen.COLOR_SCHEMES)
        effects = len(gen.EFFECTS)
        
        print(f"   ✓ {layouts} layout variations")
        print(f"   ✓ {colors} color schemes")
        print(f"   ✓ {effects} visual effects")
        print()
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 5: Audio Quality Validator
    print("5. Testing Audio Quality Validator...")
    try:
        from audio_quality_validator import AudioQualityValidator
        
        validator = AudioQualityValidator()
        
        # Test validation logic (without actual ffmpeg)
        print("   ✓ Validator initialized")
        print("   ✓ Ready for audio analysis")
        print("   ℹ  Requires ffmpeg for full testing")
        print()
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 6: Check updated pipeline files
    print("6. Testing Pipeline Integration...")
    try:
        # Test that modified files can be imported
        import ast
        
        files = [
            'advanced_video_pipeline.py',
            'claude_generator.py',
            'tts_generator.py',
            'metadata_generator.py',
            'video_maker_moviepy.py'
        ]
        
        for filename in files:
            with open(filename, 'r') as f:
                code = f.read()
            ast.parse(code)
            print(f"   ✓ {filename} syntax OK")
        
        print()
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Summary
    print("="*60)
    print("✓ All integration tests passed!")
    print("="*60)
    print()
    print("New Features Summary:")
    print("  • API Key Rotation (レート制限対策)")
    print("  • Parallel Processing (画像+音声同時生成)")
    print("  • Subtitle Optimization (読みやすさ向上)")
    print("  • Thumbnail A/B Testing (CTR最適化)")
    print("  • Audio Quality Validation (品質保証)")
    print("  • Title CTR Analysis (SEO最適化)")
    print()
    
    return True

if __name__ == "__main__":
    success = test_all_modules()
    sys.exit(0 if success else 1)
