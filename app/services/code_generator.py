# app/services/code_generator.py
from typing import Dict, List, Any, Optional
import json
import re
from app.services.llm.manager import LLMManager
from app.models.schemas import BuildRequestSchema

class CodeGenerator:
    def __init__(self):
        self.llm_manager = LLMManager()
    
    async def generate_application(
        self, 
        request: BuildRequestSchema,
        processed_attachments: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Generate application code based on the brief and requirements."""
        
        system_prompt = """You are an expert web developer. Generate a complete, working web application based on the requirements.
        Generate clean, well-commented code that follows best practices.
        The application should be a single-page application that can be deployed to GitHub Pages.
        Always include proper error handling and make the code production-ready.
        Return your response as a JSON object with file paths as keys and file contents as values.
        Example: {"index.html": "<!DOCTYPE html>...", "script.js": "// JavaScript code...", "style.css": "/* CSS code */"}
        """
        
        # Build detailed prompt
        prompt = f"""Create a web application with the following requirements:

Brief: {request.brief}

The application will be evaluated based on these checks:
{json.dumps(request.checks, indent=2)}

Task ID: {request.task}
Round: {request.round}

"""
        
        if processed_attachments:
            prompt += "\nAttachments provided:\n"
            for att in processed_attachments:
                prompt += f"- {att['name']} ({att['mime_type']})\n"
        
        prompt += """
Generate a complete application that:
1. Meets all the requirements in the brief
2. Passes all the evaluation checks
3. Handles the provided attachments appropriately
4. Is production-ready with proper error handling
5. Includes a professional README.md
6. Uses modern web development best practices

Return ONLY a valid JSON object with file paths and contents. Make sure all files needed for a complete application are included.
"""
        
        # Generate code using LLM
        response = await self.llm_manager.generate_with_fallback(
            prompt=prompt,
            system_prompt=system_prompt,
            attachments=processed_attachments
        )
        
        # Parse the response to extract code files
        files = self._parse_code_response(response.content)
        
        # Ensure required files exist
        if "index.html" not in files:
            files["index.html"] = self._generate_default_html(request)
        
        if "README.md" not in files:
            files["README.md"] = self._generate_readme(request, files)
        
        if "LICENSE" not in files:
            files["LICENSE"] = self._generate_mit_license()
        
        return files
    
    def _parse_code_response(self, response: str) -> Dict[str, str]:
        """Parse LLM response to extract code files."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Fallback: parse code blocks
        files = {}
        code_blocks = re.findall(r'```(\w+)?\n([\s\S]*?)```', response)
        
        for lang, code in code_blocks:
            if lang == 'html':
                files['index.html'] = code
            elif lang == 'javascript' or lang == 'js':
                files['script.js'] = code
            elif lang == 'css':
                files['style.css'] = code
            elif lang == 'json':
                try:
                    parsed = json.loads(code)
                    if isinstance(parsed, dict):
                        files.update(parsed)
                except:
                    pass
        
        return files
    
    def _generate_default_html(self, request: BuildRequestSchema) -> str:
        """Generate a default HTML file if not provided by LLM."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{request.task}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{request.task}</h1>
        <div id="app">
            <!-- Application content will be rendered here -->
        </div>
    </div>
    <script src="script.js"></script>
</body>
</html>"""
    
    def _generate_readme(self, request: BuildRequestSchema, files: Dict[str, str]) -> str:
        """Generate a README file."""
        return f"""# {request.task}

## Summary
This application was generated to fulfill the following requirements:
{request.brief}

## Setup
1. Clone this repository
2. Open `index.html` in a web browser
3. The application is ready to use

## Usage
The application provides the following functionality based on the requirements:
{chr(10).join(f"- {check}" for check in request.checks)}

## Code Explanation
### Files Included:
{chr(10).join(f"- `{filename}`" for filename in files.keys())}

### Key Features:
- Responsive design using Bootstrap
- Error handling for robust operation
- Clean, maintainable code structure

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Task Details
- Task ID: {request.task}
- Round: {request.round}
- Email: {request.email}
"""
    
    def _generate_mit_license(self) -> str:
        """Generate MIT License text."""
        return """MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
    
    async def update_application(
        self,
        request: BuildRequestSchema,
        existing_files: Dict[str, str],
        processed_attachments: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Update existing application based on new requirements."""
        
        system_prompt = """You are an expert web developer. Update the existing application based on new requirements.
        Preserve existing functionality while adding new features.
        Return your response as a JSON object with file paths as keys and file contents as values.
        Include ALL files, both modified and unmodified.
        """
        
        prompt = f"""Update the existing application with these new requirements:

Brief: {request.brief}

New evaluation checks:
{json.dumps(request.checks, indent=2)}

Current files in the application:
{json.dumps(list(existing_files.keys()), indent=2)}

Task ID: {request.task}
Round: {request.round}

"""
        
        if processed_attachments:
            prompt += "\nNew attachments provided:\n"
            for att in processed_attachments:
                prompt += f"- {att['name']} ({att['mime_type']})\n"
        
        prompt += """
Update the application to:
1. Meet all the new requirements in the brief
2. Pass all the new evaluation checks
3. Maintain existing functionality
4. Handle any new attachments appropriately
5. Update the README.md to reflect changes

Current code for reference:
"""
        
        # Include key existing files for context
        for filename in ['index.html', 'script.js', 'style.css']:
            if filename in existing_files:
                prompt += f"\n--- {filename} ---\n{existing_files[filename][:1000]}...\n"
        
        prompt += "\nReturn ONLY a valid JSON object with ALL file paths and their complete updated contents."
        
        response = await self.llm_manager.generate_with_fallback(
            prompt=prompt,
            system_prompt=system_prompt,
            attachments=processed_attachments
        )
        
        files = self._parse_code_response(response.content)
        
        # Merge with existing files if some are missing
        for key, value in existing_files.items():
            if key not in files and key != 'README.md':
                files[key] = value
        
        # Update README
        if "README.md" in files:
            files["README.md"] = self._update_readme(request, files["README.md"])
        
        return files
    
    def _update_readme(self, request: BuildRequestSchema, current_readme: str) -> str:
        """Update README with new round information."""
        update_section = f"""

## Round {request.round} Updates
### New Requirements:
{request.brief}

### New Checks:
{chr(10).join(f"- {check}" for check in request.checks)}
"""
        
        # Add update section before license section if exists
        if "## License" in current_readme:
            parts = current_readme.split("## License")
            return parts[0] + update_section + "\n## License" + parts[1]
        else:
            return current_readme + update_section