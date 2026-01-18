from crewai import Agent, Crew, Process, Task, LLM # Import LLM
from crewai.project import CrewBase, agent, crew, task
from invoice_validator.models.invoice_schema import ParsedInvoice
from invoice_validator.tools.raw_text_extractor_tool import RawTextExtractorTool
from invoice_validator.utils.logger import setup_logger
from invoice_validator.utils.callbacks import set_callbacks, add_log as cb_add_log, progress as cb_progress

logger = setup_logger()

@CrewBase
class InvoiceValidator():
    """InvoiceValidator crew"""

    # Paths to the YAML configuration files
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        self.logger = logger
        self.ollama_llm = LLM(
            model="ollama/qwen2.5",
            base_url="http://localhost:11434",
            temperature=0
        )

    @agent
    def document_parser(self) -> Agent:
        return Agent(
            config=self.agents_config['document_parser'],
            tools=[RawTextExtractorTool()],
            llm=self.ollama_llm,
            max_iter=1,
            verbose=True
        )

    @task
    def parse_task(self) -> Task:
        return Task(
            config=self.tasks_config['parse_task']
        )

    @task
    def structuring_task(self) -> Task:
        return Task(
            config=self.tasks_config['structuring_task'],
            context=[self.parse_task()], # Explicitly pass the output of parse_task here
            output_json=ParsedInvoice
        )

    @crew
    def crew(self) -> Crew:
        """Creates the InvoiceValidator crew"""
        return Crew(
            agents=self.agents, # Automatically created by decorators
            tasks=self.tasks,   # Automatically created by decorators
            process=Process.sequential,
            verbose=True,
        )

    def validate_invoice(self, file_path, file_type, progress, add_log):
        """Run the complete validation workflow"""
        self.logger.info(f"Starting validation for {file_path}")
        # Make callbacks globally available to tools/agents
        set_callbacks(progress, add_log)

        cb_progress(0.1, desc="Initializing agents...")
        cb_add_log("🤖 Initializing CrewAI agents...")

        try:
            # Inputs must match the keys used in YAML (e.g., {file_path})
            inputs = {
                'file_path': file_path,
                'file_type': file_type
            }
            
            # Use self.crew() to get the instance and kickoff
            result = self.crew().kickoff(inputs=inputs)
            
            return {
                'status': 'completed',
                'raw': str(result)
            }
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
        
