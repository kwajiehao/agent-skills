"""Output examples remain source-linked, honest about execution, and safe to render."""

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SKILL=Path(__file__).resolve().parents[1]

def load(name, filename):
    spec=importlib.util.spec_from_file_location(name, SKILL/'scripts'/filename)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

validator=load('output_validator','validate_walkthrough.py')
renderer=load('output_renderer','render_walkthrough.py')

class OutputExampleTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((SKILL/'assets/example-data.json').read_text())

    def errors(self, data):
        result=validator.Validation()
        validator.validate_data(data,result)
        return result.errors

    def test_legacy_artifacts_without_examples_remain_valid(self):
        self.data.pop('examples',None)
        for step in self.data['steps']: step.pop('example_ids',None)
        self.assertEqual(self.errors(self.data),[])

    def test_invalid_references_and_unlinked_examples_are_rejected(self):
        for field,value in [('id','unattached'),('evidence_code_ids',['missing-code'])]:
            with self.subTest(field=field):
                data=copy.deepcopy(self.data)
                data['examples'][0][field]=value
                self.assertTrue(self.errors(data))
        data=copy.deepcopy(self.data)
        data['steps'][0]['example_ids']=['missing-example']
        self.assertTrue(self.errors(data))
        data=copy.deepcopy(self.data)
        data['examples'].append(copy.deepcopy(data['examples'][0]))
        self.assertTrue(self.errors(data))

    def test_observed_output_requires_concrete_execution_record(self):
        self.data['examples'][0]['provenance']='observed'
        self.assertTrue(any('execution' in error for error in self.errors(self.data)))
        self.data['examples'][0]['execution']='Local fixture command; retained stdout in fixture/run.log'
        self.assertEqual(self.errors(self.data),[])

    def test_malformed_output_metadata_is_rejected_without_crashing(self):
        for key,value in [('stage','input'),('provenance','verified'),('side','baseish'),('content',{}),('evidence_code_ids',None)]:
            with self.subTest(key=key):
                data=copy.deepcopy(self.data)
                data['examples'][0][key]=value
                self.assertTrue(self.errors(data))

    def test_render_roundtrip_preserves_literal_output_instead_of_html(self):
        payload='</script><img src=x onerror=alert(1)> & "quoted"'
        self.data['examples'][0]['content']=payload
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'data.json'; path.write_text(json.dumps(self.data))
            output=Path(temp)/'index.html'
            renderer.render(path,output,SKILL/'assets/walkthrough-template.html')
            html=output.read_text()
            self.assertNotIn(payload,html)
            result=validator.Validation()
            restored=validator.extract_data(html,result)
            self.assertEqual(restored['examples'][0]['content'],payload)
            self.assertEqual(result.errors,[])

    @unittest.skipUnless(shutil.which('node'),'Node is needed for the isolated DOM test')
    def test_step_selection_replaces_outputs_and_keeps_payload_as_text(self):
        template=(SKILL/'assets/walkthrough-template.html').read_text()
        start=template.index('      function renderExamples(step) {')
        end=template.index('      function setStep(index) {',start)
        function=template[start:end]
        # Execute the actual output renderer with a minimal text-only DOM.
        harness="""
const assert=require('node:assert/strict');
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.textContent='';this.hidden=false;}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;}
  set innerHTML(_){throw new Error('Untrusted output must never be parsed as HTML');}
}
const create=(tag,cls,text)=>{const e=new Element(tag);e.className=cls;if(text!==undefined)e.textContent=text;return e;};
const panel=new Element('section');
const byId=()=>panel;
const link=(label,url,cls)=>{const e=create('a',cls,label);e.href=url;return e;};
const findCode=id=>data.code.find(c=>c.id===id);
const text=e=>e.textContent+e.children.map(text).join(' ');
"""
        data=copy.deepcopy(self.data)
        data['examples'][0]['content']='<img src=x onerror=alert(1)>'
        first=data['examples'][0]
        script=harness+'\nconst data='+json.dumps(data)+';\n'+function
        script+='\nrenderExamples({example_ids:['+json.dumps(first['id'])+']});'
        script+='\nassert.equal(panel.hidden,false); assert.equal(panel.children.length,2);'
        script+='\nassert.ok(text(panel).includes("Worked example")); assert.ok(text(panel).includes("<img src=x onerror=alert(1)>"));'
        script+='\nassert.ok(text(panel).includes('+json.dumps(first['location'])+'));'
        script+='\nrenderExamples({}); assert.equal(panel.hidden,true); assert.equal(panel.children.length,0);'
        result=subprocess.run(['node','-e',script],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__': unittest.main()
