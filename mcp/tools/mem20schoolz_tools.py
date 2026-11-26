"""mem20schoolz MCP tools — training, certification, apprenticeship."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    if _REPO_ROOT not in sys.path: sys.path.insert(0,_REPO_ROOT)
    import mem20schoolz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
def _obj(props,required=None):
    return {"type":"object","properties":props,"required":required or []}
_S={"type":"string"}
_N={"type":"number"}
_A={"type":"array"}
_O={"type":"object"}
class SchoolzToolsMixin:
    def register_schoolz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        t=self.tools
        t["mem20schoolz_status"]=mt.Tool(name="mem20schoolz_status",title="Schoolz Status",description="Report the school store counts.",inputSchema=_obj({}))
        t["mem20schoolz_doctor"]=mt.Tool(name="mem20schoolz_doctor",title="Schoolz Doctor",description="Probe the school store.",inputSchema=_obj({}))
        t["mem20schoolz_list_courses"]=mt.Tool(name="mem20schoolz_list_courses",title="List Courses",description="List every course in the catalog.",inputSchema=_obj({}))
        t["mem20schoolz_get_lesson"]=mt.Tool(name="mem20schoolz_get_lesson",title="Get Lesson",description="Return one lesson from one course.",inputSchema=_obj({"course_id":_S,"lesson_id":_S},["course_id","lesson_id"]))
        t["mem20schoolz_create_course"]=mt.Tool(name="mem20schoolz_create_course",title="Create Course",description="Add a course with lessons [{title, content}].",inputSchema=_obj({"title":_S,"skill":_S,"lessons":_A,"description":_S},["title","skill","lessons"]))
        t["mem20schoolz_create_learning_path"]=mt.Tool(name="mem20schoolz_create_learning_path",title="Create Learning Path",description="Build a learning path for a learner toward a goal skill.",inputSchema=_obj({"learner":_S,"goal":_S,"course_ids":_A},["learner","goal"]))
        t["mem20schoolz_track_progress"]=mt.Tool(name="mem20schoolz_track_progress",title="Track Progress",description="Record a learner's progress on one lesson.",inputSchema=_obj({"learner":_S,"course_id":_S,"lesson_id":_S,"status":_S},["learner","course_id","lesson_id"]))
        t["mem20schoolz_skill_level"]=mt.Tool(name="mem20schoolz_skill_level",title="Skill Level",description="Level 0-5 for a skill, optionally for one learner.",inputSchema=_obj({"skill":_S,"learner":_S},["skill"]))
        t["mem20schoolz_mentor_match"]=mt.Tool(name="mem20schoolz_mentor_match",title="Mentor Match",description="Find mentors who teach a skill.",inputSchema=_obj({"learner":_S,"skill":_S},["learner","skill"]))
        t["mem20schoolz_evaluate_task"]=mt.Tool(name="mem20schoolz_evaluate_task",title="Evaluate Task",description="Record an evaluation of a learner on a task (score 0-100).",inputSchema=_obj({"learner":_S,"task":_S,"score":_N,"notes":_S},["learner","task","score"]))
        t["mem20schoolz_progression_plan"]=mt.Tool(name="mem20schoolz_progression_plan",title="Progression Plan",description="A plan for a learner to reach a goal skill.",inputSchema=_obj({"learner":_S,"goal":_S},["learner","goal"]))
        t["mem20schoolz_mentorship_hours"]=mt.Tool(name="mem20schoolz_mentorship_hours",title="Mentorship Hours",description="Total mentorship hours, optionally filtered.",inputSchema=_obj({"learner":_S,"mentor":_S}))
        t["mem20schoolz_register_mentor"]=mt.Tool(name="mem20schoolz_register_mentor",title="Register Mentor",description="Register a mentor and the skills they teach.",inputSchema=_obj({"name":_S,"skills":_A},["name","skills"]))
        t["mem20schoolz_log_session"]=mt.Tool(name="mem20schoolz_log_session",title="Log Session",description="Log a mentorship session.",inputSchema=_obj({"learner":_S,"mentor":_S,"skill":_S,"hours":_N},["learner","mentor","skill","hours"]))
        t["mem20schoolz_list_exams"]=mt.Tool(name="mem20schoolz_list_exams",title="List Exams",description="List every exam.",inputSchema=_obj({}))
        t["mem20schoolz_create_exam"]=mt.Tool(name="mem20schoolz_create_exam",title="Create Exam",description="Add an exam with questions [{prompt, choices, answer}].",inputSchema=_obj({"title":_S,"skill":_S,"questions":_A,"course_id":_S,"passing_score":_N},["title","skill","questions"]))
        t["mem20schoolz_take_exam"]=mt.Tool(name="mem20schoolz_take_exam",title="Take Exam",description="Score answers {question_id: answer} against the exam key.",inputSchema=_obj({"learner":_S,"exam_id":_S,"answers":_O},["learner","exam_id","answers"]))
        t["mem20schoolz_issue_credential"]=mt.Tool(name="mem20schoolz_issue_credential",title="Issue Credential",description="Issue a credential for a passed exam.",inputSchema=_obj({"learner":_S,"exam_id":_S},["learner","exam_id"]))
        t["mem20schoolz_verify_credential"]=mt.Tool(name="mem20schoolz_verify_credential",title="Verify Credential",description="Check a credential id against the store and its hash.",inputSchema=_obj({"credential_id":_S},["credential_id"]))
    def _call(self,fn,args,keys):
        try:
            f=getattr(_load(),fn)
            return _d(f(**{k:args[k] for k in keys if k in args}))
        except Exception as e: return _d({"ok":False,"error":str(e)})
    async def _mem20schoolz_status(self,args:Dict[str,Any])->str: return self._call("estate_context",args,[])
    async def _mem20schoolz_doctor(self,args:Dict[str,Any])->str: return self._call("probe",args,[])
    async def _mem20schoolz_list_courses(self,args:Dict[str,Any])->str: return self._call("list_courses",args,[])
    async def _mem20schoolz_get_lesson(self,args:Dict[str,Any])->str: return self._call("get_lesson",args,["course_id","lesson_id"])
    async def _mem20schoolz_create_course(self,args:Dict[str,Any])->str: return self._call("create_course",args,["title","skill","lessons","description"])
    async def _mem20schoolz_create_learning_path(self,args:Dict[str,Any])->str: return self._call("create_learning_path",args,["learner","goal","course_ids"])
    async def _mem20schoolz_track_progress(self,args:Dict[str,Any])->str: return self._call("track_progress",args,["learner","course_id","lesson_id","status"])
    async def _mem20schoolz_skill_level(self,args:Dict[str,Any])->str: return self._call("skill_level",args,["skill","learner"])
    async def _mem20schoolz_mentor_match(self,args:Dict[str,Any])->str: return self._call("mentor_match",args,["learner","skill"])
    async def _mem20schoolz_evaluate_task(self,args:Dict[str,Any])->str: return self._call("evaluate_task",args,["learner","task","score","notes"])
    async def _mem20schoolz_progression_plan(self,args:Dict[str,Any])->str: return self._call("progression_plan",args,["learner","goal"])
    async def _mem20schoolz_mentorship_hours(self,args:Dict[str,Any])->str: return self._call("mentorship_hours",args,["learner","mentor"])
    async def _mem20schoolz_register_mentor(self,args:Dict[str,Any])->str: return self._call("register_mentor",args,["name","skills"])
    async def _mem20schoolz_log_session(self,args:Dict[str,Any])->str: return self._call("log_session",args,["learner","mentor","skill","hours"])
    async def _mem20schoolz_list_exams(self,args:Dict[str,Any])->str: return self._call("list_exams",args,[])
    async def _mem20schoolz_create_exam(self,args:Dict[str,Any])->str: return self._call("create_exam",args,["title","skill","questions","course_id","passing_score"])
    async def _mem20schoolz_take_exam(self,args:Dict[str,Any])->str: return self._call("take_exam",args,["learner","exam_id","answers"])
    async def _mem20schoolz_issue_credential(self,args:Dict[str,Any])->str: return self._call("issue_credential",args,["learner","exam_id"])
    async def _mem20schoolz_verify_credential(self,args:Dict[str,Any])->str: return self._call("verify_credential",args,["credential_id"])
