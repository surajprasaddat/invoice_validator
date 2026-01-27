from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from invoice_validator.models.invoice_schema import ParsedInvoice
from invoice_validator.utils.logger import setup_logger
from invoice_validator.utils.callbacks import set_callbacks, add_log as cb_add_log, progress as cb_progress
from invoice_validator.tools.validation_tool import ValidationTool
import os

logger = setup_logger()

@CrewBase
class InvoiceValidator():
    """InvoiceValidator crew with MAXIMUM real-time updates using step callbacks"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        self.logger = logger
        model_name = os.environ.get("MODEL", "openrouter/openai/gpt-4o-mini")
        self.ollama_llm = LLM(
            model=model_name,
            temperature=0,
            max_tokens=2048
        )
        self.validation_tool = ValidationTool()
        self.current_update = {
            'report': '',
            'logs': '',
            'json_data': {}
        }

    @agent
    def document_parser(self) -> Agent:
        return Agent(
            config=self.agents_config['document_parser'],
            llm=self.ollama_llm,
            verbose=True
        )
    
    @agent
    def validator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['validator_agent'],
            llm=self.ollama_llm,
            tools=[self.validation_tool],
            verbose=True
        )
    
    @agent
    def reporter_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['reporter_agent'],
            llm=self.ollama_llm,
            verbose=True
        )

    @task
    def parse_task(self) -> Task:
        return Task(
            config=self.tasks_config['parse_task'],
            output_json=ParsedInvoice
        )
    
    @task
    def validator_task(self) -> Task:
        return Task(
            config=self.tasks_config['validator_task']
        )
    
    @task
    def reporter_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporter_task']
        )

    def create_step_callback(self, update_queue):
        """
        Create a step callback that yields updates in real-time.
        This callback is called by CrewAI after each agent step.
        """
        def step_callback(step_output):
            """Called after each agent reasoning step"""
            try:
                # Log the step
                if hasattr(step_output, 'task') and step_output.task:
                    task_desc = step_output.task.description[:50] + "..."
                    logs = cb_add_log(f"🔄 Processing: {task_desc}")
                    self.current_update['logs'] = logs
                    update_queue.append(self.current_update.copy())
                
                # If step has output, log it
                if hasattr(step_output, 'output') and step_output.output:
                    output_preview = str(step_output.output)[:100]
                    logs = cb_add_log(f"📝 Output: {output_preview}...")
                    self.current_update['logs'] = logs
                    update_queue.append(self.current_update.copy())
                    
            except Exception as e:
                self.logger.error(f"Step callback error: {e}")
        
        return step_callback

    def validate_invoice_streaming(self, invoice_raw_data, progress, add_log):
        """
        ULTRA REAL-TIME VERSION: Uses step callbacks for maximum granularity.
        Yields updates after EVERY agent step.
        """
        
        set_callbacks(progress, add_log)
        update_queue = []
        
        try:
            # Initialize
            progress(0.1, desc="Initializing agents...")
            self.current_update['logs'] = add_log("🤖 Initializing CrewAI agents...")
            yield self.current_update.copy()
            
            # TASK 1: PARSE INVOICE with step callback
            progress(0.2, desc="Parsing invoice...")
            self.current_update['logs'] = add_log("📝 Starting Document Parser Agent...")
            yield self.current_update.copy()
            
            parse_crew = Crew(
                agents=[self.document_parser()],
                tasks=[self.parse_task()],
                process=Process.sequential,
                verbose=True,
                step_callback=self.create_step_callback(update_queue)
            )
            
            # Yield any queued updates during parsing
            parse_result = parse_crew.kickoff(
                inputs={'invoice_raw_data': invoice_raw_data}
            )
            
            # Yield all step updates
            for update in update_queue:
                yield update
            update_queue.clear()
            
            # Extract parsed JSON
            parsed_json = None
            for task_output in parse_result.tasks_output:
                if hasattr(task_output, 'json_dict') and task_output.json_dict:
                    parsed_json = ParsedInvoice(**task_output.json_dict)
                    break
                elif hasattr(task_output, 'pydantic') and task_output.pydantic:
                    parsed_json = task_output.pydantic
                    break
            
            if not parsed_json:
                raise ValueError("Parser failed to return invoice JSON")
            
            confidence = parsed_json.confidence or 0
            progress(0.4, desc=f"Parsing complete ({confidence}% confidence)")
            self.current_update['logs'] = add_log(f"✅ Parsing complete - Confidence: {confidence}%")
            self.current_update['json_data'] = parsed_json.model_dump() if hasattr(parsed_json, 'model_dump') else {}
            
            # YIELD PARSED JSON IMMEDIATELY
            yield self.current_update.copy()
            
            # CONDITIONAL ROUTING
            
            if confidence < 70:
                # LOW CONFIDENCE PATH
                self.current_update['logs'] = add_log("⚠️ Low confidence → Generating data quality report")
                yield self.current_update.copy()
                
                progress(0.6, desc="Generating report...")
                
                reporter_crew = Crew(
                    agents=[self.reporter_agent()],
                    tasks=[self.reporter_task()],
                    process=Process.sequential,
                    verbose=True,
                    step_callback=self.create_step_callback(update_queue)
                )
                
                reporter_result = reporter_crew.kickoff(
                    inputs={
                        'parsed_invoice': parsed_json.model_dump(),
                        'validation_results': None
                    }
                )
                
                # Yield step updates
                for update in update_queue:
                    yield update
                update_queue.clear()
                
                final_report = str(reporter_result.raw)
                
            else:
                # HIGH CONFIDENCE PATH
                self.current_update['logs'] = add_log("✅ High confidence → Running validation")
                yield self.current_update.copy()
                
                # TASK 2: VALIDATE with step callback
                progress(0.5, desc="Validating compliance...")
                self.current_update['logs'] = add_log("🔍 Starting Validator Agent...")
                yield self.current_update.copy()
                
                validator_crew = Crew(
                    agents=[self.validator_agent()],
                    tasks=[self.validator_task()],
                    process=Process.sequential,
                    verbose=True,
                    step_callback=self.create_step_callback(update_queue)
                )
                
                validator_result = validator_crew.kickoff(
                    inputs={'parsed_invoice': parsed_json.model_dump()}
                )
                
                # Yield step updates
                for update in update_queue:
                    yield update
                update_queue.clear()
                
                progress(0.7, desc="Validation complete")
                self.current_update['logs'] = add_log("✅ Validation complete")
                yield self.current_update.copy()
                
                # TASK 3: REPORT with step callback
                progress(0.8, desc="Generating report...")
                self.current_update['logs'] = add_log("📊 Starting Reporter Agent...")
                yield self.current_update.copy()
                
                reporter_crew = Crew(
                    agents=[self.reporter_agent()],
                    tasks=[self.reporter_task()],
                    process=Process.sequential,
                    verbose=True,
                    step_callback=self.create_step_callback(update_queue)
                )
                
                reporter_result = reporter_crew.kickoff(
                    inputs={
                        'parsed_invoice': parsed_json.model_dump(),
                        'validation_results': str(validator_result.raw)
                    }
                )
                
                # Yield step updates
                for update in update_queue:
                    yield update
                update_queue.clear()
                
                final_report = str(reporter_result.raw)
            
            # FINAL OUTPUT
            progress(0.9, desc="Finalizing...")
            self.current_update['logs'] = add_log("💾 Saving report...")
            self.current_update['report'] = final_report
            yield self.current_update.copy()
            
            # Save report
            from datetime import datetime
            report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            report_path = os.path.join("outputs/reports", report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(final_report)
            
            progress(1.0, desc="Complete!")
            self.current_update['logs'] = add_log(f"✅ Report saved: {report_filename}")
            self.current_update['logs'] = add_log("🎉 Validation complete!")
            
            yield self.current_update.copy()
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            self.logger.error(f"Validation failed: {str(e)}")
            self.current_update['logs'] = add_log(f"❌ ERROR: {str(e)}")
            self.current_update['report'] = f"Validation failed: {str(e)}"
            yield self.current_update.copy()

    def validate_invoice(self, invoice_raw_data, progress, add_log):
        """Non-streaming version (backward compatibility)"""
        final_result = None
        for update in self.validate_invoice_streaming(invoice_raw_data, progress, add_log):
            final_result = update
        
        if final_result:
            return {
                'status': 'completed',
                'raw': final_result.get('report', ''),
                'parsed_json': final_result.get('json_data', {})
            }
        else:
            return {'status': 'failed', 'error': 'No result generated'}