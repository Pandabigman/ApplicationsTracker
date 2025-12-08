"""
Setup script for Job Tracker Backend
Helps initialize the application with necessary configuration
"""

import os
from pathlib import Path
import sys

def setup_environment():
    """Setup the environment for the application"""
    print("=" * 60)
    print("Job Tracker Backend Setup")
    print("=" * 60)
    print()

    # Check if .env exists
    env_path = Path(__file__).parent / ".env"
    env_example_path = Path(__file__).parent / ".env.example"

    if not env_path.exists():
        print("Creating .env file...")
        if env_example_path.exists():
            # Copy example to .env
            with open(env_example_path, 'r') as f:
                content = f.read()
            with open(env_path, 'w') as f:
                f.write(content)
            print("✓ Created .env file from .env.example")
        else:
            # Create basic .env
            with open(env_path, 'w') as f:
                f.write("# OpenAI API Key for GPT-4 scraping\n")
                f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
            print("✓ Created .env file")
    else:
        print("✓ .env file already exists")

    print()
    print("=" * 60)
    print("Configuration")
    print("=" * 60)
    print()

    # Ask for OpenAI API key
    print("To enable GPT-4 job scraping, you need an OpenAI API key.")
    print("Get one at: https://platform.openai.com/api-keys")
    print()

    # Read current .env
    with open(env_path, 'r') as f:
        env_content = f.read()

    if 'your_openai_api_key_here' in env_content or 'OPENAI_API_KEY=' not in env_content:
        print("Your .env file doesn't have a valid OpenAI API key configured.")
        response = input("Would you like to add it now? (y/n): ").strip().lower()

        if response == 'y':
            api_key = input("Enter your OpenAI API key: ").strip()
            if api_key:
                # Update .env file
                lines = env_content.split('\n')
                new_lines = []
                found = False
                for line in lines:
                    if line.startswith('OPENAI_API_KEY='):
                        new_lines.append(f'OPENAI_API_KEY={api_key}')
                        found = True
                    else:
                        new_lines.append(line)

                if not found:
                    new_lines.append(f'OPENAI_API_KEY={api_key}')

                with open(env_path, 'w') as f:
                    f.write('\n'.join(new_lines))

                print("✓ OpenAI API key saved to .env")
            else:
                print("⚠ No API key provided. You can add it manually to .env later.")
        else:
            print("⚠ You can add your API key manually to .env later.")
    else:
        print("✓ OpenAI API key is configured")

    print()
    print("=" * 60)
    print("Database Setup")
    print("=" * 60)
    print()

    # Create data directory
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    print("✓ Data directory created")

    db_path = data_dir / "jobtracker.db"
    if db_path.exists():
        print(f"✓ Database already exists at: {db_path}")
    else:
        print("Database will be created automatically on first run")

    print()
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Start the server: cd app && python main.py")
    print("3. Visit: http://localhost:8000/docs")
    print()
    print("Optional: Run migration if you have PostgreSQL data:")
    print("   python migrate_to_sqlite.py")
    print()

if __name__ == "__main__":
    try:
        setup_environment()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during setup: {e}")
        sys.exit(1)
