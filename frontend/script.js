const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

const initialData = {
  Students: [
    {name:"Aarav Sharma", id:"STU-2026-001", course:"BCA", year:"1st Year", status:"Active"},
    {name:"Priya Kumar", id:"STU-2026-002", course:"BBA", year:"2nd Year", status:"Active"},
    {name:"Rahul Mishra", id:"STU-2026-003", course:"B.Sc.", year:"1st Year", status:"Pending"},
    {name:"Neha Gupta", id:"STU-2026-004", course:"BCA", year:"3rd Year", status:"Active"}
  ],
  Teachers: [
    {name:"Dr. Amit Verma", id:"TCH-101", department:"Computer Science", email:"amit@example.com", status:"Active"},
    {name:"Ms. Pooja Singh", id:"TCH-102", department:"Commerce", email:"pooja@example.com", status:"Active"},
    {name:"Mr. Rakesh Kumar", id:"TCH-103", department:"Mathematics", email:"rakesh@example.com", status:"On Leave"}
  ],
  Parents: [
    {name:"Suresh Sharma", student:"Aarav Sharma", phone:"9876543210", relation:"Father", status:"Verified"},
    {name:"Meena Kumar", student:"Priya Kumar", phone:"9876543211", relation:"Mother", status:"Verified"}
  ],
  Courses: [
    {name:"Bachelor of Computer Applications", code:"BCA", duration:"3 Years", department:"Computer Science", status:"Active"},
    {name:"Bachelor of Business Administration", code:"BBA", duration:"3 Years", department:"Management", status:"Active"},
    {name:"Bachelor of Science", code:"BSC", duration:"3 Years", department:"Science", status:"Active"}
  ],
  Admissions: [
    {name:"Ankit Yadav", application:"APP-2026-014", course:"BCA", date:"2026-10-25", status:"Under Review"},
    {name:"Simran Das", application:"APP-2026-015", course:"BBA", date:"2026-10-27", status:"Approved"}
  ],
  Attendance: [
    {name:"Aarav Sharma", id:"STU-2026-001", date:"2026-11-01", attendance:"Present"},
    {name:"Priya Kumar", id:"STU-2026-002", date:"2026-11-01", attendance:"Present"},
    {name:"Rahul Mishra", id:"STU-2026-003", date:"2026-11-01", attendance:"Absent"}
  ],
  Examinations: [
    {name:"Mid-term Examination", course:"BCA / BBA", date:"2026-11-05", venue:"Main Block", status:"Scheduled"},
    {name:"Practical Examination", course:"BCA", date:"2026-11-12", venue:"Computer Lab", status:"Scheduled"}
  ],
  Results: [
    {name:"Aarav Sharma", course:"BCA", semester:"Semester 1", percentage:"88%", status:"Published"},
    {name:"Priya Kumar", course:"BBA", semester:"Semester 3", percentage:"91%", status:"Published"}
  ],
  "Fees Management": [
    {name:"Aarav Sharma", id:"STU-2026-001", amount:"₹25,000", dueDate:"2026-11-10", status:"Paid"},
    {name:"Rahul Mishra", id:"STU-2026-003", amount:"₹25,000", dueDate:"2026-11-10", status:"Pending"}
  ],
  Notices: [
    {title:"Mid-term exam schedule released", date:"2026-10-28", audience:"All Students", status:"Published"},
    {title:"Fee payment deadline: November 10", date:"2026-10-25", audience:"Students & Parents", status:"Published"}
  ],
  Settings: [
    {name:"College Profile", detail:"Update institution details", status:"Available"},
    {name:"User Preferences", detail:"Manage dashboard preferences", status:"Available"}
  ]
};
const data = JSON.parse(JSON.stringify(initialData));
const apiResources = {Students:"students", Teachers:"teachers", Parents:"parents"};
let currentPage = "Dashboard";
let editIndex = null;
let toastTimer;
let backendConnected = true;

const fieldConfig = {
  Students: [["name","Student name"],["id","Student ID"],["course","Course"],["year","Year"],["status","Status"]],
  Teachers: [["name","Teacher name"],["id","Teacher ID"],["department","Department"],["email","Email"],["status","Status"]],
  Parents: [["name","Parent name"],["student","Student name"],["phone","Phone"],["relation","Relation"],["status","Status"]],
  Courses: [["name","Course name"],["code","Course code"],["duration","Duration"],["department","Department"],["status","Status"]],
  Admissions: [["name","Applicant name"],["application","Application ID"],["course","Course"],["date","Application date"],["status","Status"]],
  Attendance: [["name","Student name"],["id","Student ID"],["date","Date"],["attendance","Attendance"]],
  Examinations: [["name","Exam name"],["course","Course"],["date","Exam date"],["venue","Venue"],["status","Status"]],
  Results: [["name","Student name"],["course","Course"],["semester","Semester"],["percentage","Percentage"],["status","Status"]],
  "Fees Management": [["name","Student name"],["id","Student ID"],["amount","Fee amount"],["dueDate","Due date"],["status","Payment status"]],
  Notices: [["title","Notice title"],["date","Date"],["audience","Audience"],["status","Status"]],
  Settings: [["name","Setting"],["detail","Description"],["status","Status"]]
};
const titles = {
  Students:"Student Directory", Teachers:"Teacher Directory", Parents:"Parent Directory",
  Courses:"Course Management", Admissions:"Admission Applications", Attendance:"Attendance Records",
  Examinations:"Examination Schedule", Results:"Student Results", "Fees Management":"Fee Records",
  Notices:"College Notices", Settings:"System Settings"
};
function showToast(message){
  const toast=$("#toast"); toast.textContent=message; toast.classList.add("show");
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>toast.classList.remove("show"),2600);
}
function csrfToken(){
  return document.cookie.split("; ").find(cookie=>cookie.startsWith("csrftoken="))?.split("=")[1]||"";
}
async function apiRequest(page, method="GET", recordId=null, payload=null){
  const resource=apiResources[page];
  const url=`/api/${resource}/${recordId===null?"":`${recordId}/`}`;
  const options={method,headers:{}};
  if(payload){options.headers["Content-Type"]="application/json";options.body=JSON.stringify(payload);}
  if(method!=="GET")options.headers["X-CSRFToken"]=csrfToken();
  const response=await fetch(url,options);
  if(response.status===401){window.location.assign("/");throw new Error("Redirecting to dashboard login.");}
  const result=response.status===204?{}:await response.json();
  if(!response.ok)throw new Error(result.error||"The server could not complete this request.");
  return result;
}
async function loadBackendRecords(){
  const results=await Promise.all(Object.keys(apiResources).map(async page=>{
    try{data[page]=await apiRequest(page);return true;}
    catch{return false;}
  }));
  backendConnected=results.every(Boolean);
  const note=$("#backendNote");
  if(note&&!backendConnected)note.textContent="Backend unavailable. Displayed records may be sample data; changes cannot be saved.";
  updateDashboardRecords();
  if(currentPage!=="Dashboard")renderSection();
  if(!backendConnected)showToast("Could not load all saved records from the backend.");
}
function updateDashboardRecords(){
  const stats=$$(".stats-grid .stat-card h2");
  if(stats[0])stats[0].textContent=(data.Students||[]).length.toLocaleString();
  if(stats[1])stats[1].textContent=(data.Teachers||[]).length.toLocaleString();
  const body=$(".table-panel tbody");
  if(!body)return;
  const students=(data.Students||[]).slice(0,4);
  body.innerHTML=students.length?students.map((student,index)=>{
    const initials=student.name.split(/\s+/).map(part=>part[0]).join("").slice(0,2).toUpperCase();
    return `<tr><td><div class="person"><span class="person-avatar a${index+1}">${escapeHTML(initials)}</span><span><strong>${escapeHTML(student.name)}</strong><small>${escapeHTML(student.id)}</small></span></div></td><td>${escapeHTML(student.course)}</td><td>${escapeHTML(student.year)}</td><td>${statusBadge(student.status)}</td></tr>`;
  }).join(""):`<tr><td colspan="4" class="empty-state">No students have been added.</td></tr>`;
}
function navigate(page){
  currentPage=page;
  $$(".nav-item[data-page]").forEach(btn=>btn.classList.toggle("active",btn.dataset.page===page));
  $("#breadcrumb").textContent=page;
  $("#pageTitle").textContent=page==="Dashboard"?"Dashboard Overview":page;
  $("#pageSubtitle").textContent=page==="Dashboard"?"Welcome back! Here's what's happening at your college today.":`View and manage ${page.toLowerCase()} information.`;
  $("#dashboardPage").classList.toggle("hidden",page!=="Dashboard");
  $("#sectionPage").classList.toggle("hidden",page==="Dashboard");
  if(page!=="Dashboard") renderSection();
  $("#sidebar").classList.remove("open");
  window.scrollTo({top:0,behavior:"smooth"});
}
function columnsFor(page){
  const records=data[page]||[];
  return records.length?Object.keys(records[0]).filter(key=>key!=="pk"):(fieldConfig[page]||[]).map(x=>x[0]);
}
function pretty(key){return key.replace(/([A-Z])/g," $1").replace(/^./,c=>c.toUpperCase());}
function escapeHTML(value){return String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function statusBadge(value){
  const v=String(value||"").toLowerCase();
  let cls=(v.includes("active")||v.includes("paid")||v.includes("present")||v.includes("verified")||v.includes("published")||v.includes("approved")||v.includes("available"))?"success":(v.includes("pending")||v.includes("review")||v.includes("leave")||v.includes("absent"))?"warning":"neutral";
  return `<span class="badge ${cls}">${escapeHTML(value)}</span>`;
}
function renderSection(){
  $("#sectionHeading").textContent=titles[currentPage]||currentPage;
  $("#sectionDescription").textContent=`Manage ${currentPage.toLowerCase()} records from one place.`;
  const columns=columnsFor(currentPage);
  $("#sectionTableHead").innerHTML=`<tr>${columns.map(c=>`<th>${escapeHTML(pretty(c).toUpperCase())}</th>`).join("")}<th>ACTIONS</th></tr>`;
  const query=($("#tableSearch").value||"").trim().toLowerCase();
  const rows=(data[currentPage]||[]).map((row,index)=>({row,index})).filter(({row})=>Object.values(row).some(v=>String(v).toLowerCase().includes(query)));
  $("#recordCount").textContent=`${rows.length} record${rows.length===1?"":"s"}`;
  $("#sectionTableBody").innerHTML=rows.length?rows.map(({row,index})=>`<tr>${columns.map(c=>`<td>${c.toLowerCase().includes("status")||c==="attendance"?statusBadge(row[c]):escapeHTML(row[c])}</td>`).join("")}<td><button class="row-action" data-edit="${index}">Edit</button><button class="row-action delete-action" data-delete="${index}">Delete</button></td></tr>`).join(""):`<tr><td colspan="${columns.length+1}" class="empty-state">No matching records found.</td></tr>`;
  const note=$("#backendNote");
  if(note&&apiResources[currentPage])note.textContent=backendConnected?"Changes to this section are saved to the database.":"Backend unavailable. Changes cannot be saved.";
  else if(note)note.textContent="This section uses demo data and is not saved to the database.";
}
function openDialog(index=null){
  editIndex=index;
  const fields=[...(fieldConfig[currentPage]||[])];
  if(!fields.length){showToast("This section is for viewing settings in this demo.");return;}
  if(["Students","Teachers","Parents"].includes(currentPage))fields.push(["password",index===null?"Password":"New password"]);
  $("#dialogTitle").textContent=index===null?`Add ${currentPage.replace(/s$/,"")} record`:"Edit record";
  $("#formFields").previousElementSibling.querySelector("p").textContent=["Students","Teachers","Parents"].includes(currentPage)
    ?(index===null?`Set the password this ${currentPage.slice(0,-1).toLowerCase()} will use to sign in with their ${currentPage==="Parents"?"Parent ID":currentPage==="Students"?"Student ID":"Teacher ID"}.`:"Leave the password blank to keep the current one.")
    :"Enter the details below.";
  const record=index===null?{}:data[currentPage][index];
  $("#formFields").innerHTML=fields.map(([key,label])=>{
    const val=record[key]||"";
    if(key==="password"){
      return `<div class="form-field"><label for="field-password">${label}</label><input id="field-password" name="password" type="password" autocomplete="new-password" ${index===null?"required minlength=\"8\"":""} placeholder="${index===null?"At least 8 characters":"Leave blank to keep current password"}" /></div>`;
    }
    if(key==="status"||key==="attendance"){
      const opts=key==="attendance"?["Present","Absent","Late"]:["Active","Pending","Approved","Under Review","Paid","Unpaid","Published","Verified","Scheduled","On Leave"];
      return `<div class="form-field"><label for="field-${key}">${label}</label><select id="field-${key}" name="${key}">${[...new Set([val,...opts].filter(Boolean))].map(o=>`<option ${o===val?"selected":""}>${escapeHTML(o)}</option>`).join("")}</select></div>`;
    }
    const type=key.toLowerCase().includes("date")?"date":key==="email"?"email":"text";
    return `<div class="form-field"><label for="field-${key}">${label}</label><input id="field-${key}" name="${key}" type="${type}" value="${escapeHTML(val)}" ${key==="name"||key==="title"?"required":""} placeholder="Enter ${label.toLowerCase()}" /></div>`;
  }).join("");
  $("#recordDialog").showModal();
}
function closeDialog(){$("#recordDialog").close();}
$("#nav").addEventListener("click",e=>{const btn=e.target.closest("[data-page]");if(btn)navigate(btn.dataset.page);});
document.addEventListener("click",async e=>{
  const goto=e.target.closest("[data-goto]");if(goto)navigate(goto.dataset.goto);
  const edit=e.target.closest("[data-edit]");if(edit)openDialog(Number(edit.dataset.edit));
  const del=e.target.closest("[data-delete]");if(del){
    const idx=Number(del.dataset.delete);
    const name=data[currentPage][idx]?.name||data[currentPage][idx]?.title||"this record";
    if(confirm(`Delete ${name}?`)){
      try{
        const row=data[currentPage][idx];
        if(apiResources[currentPage])await apiRequest(currentPage,"DELETE",row.pk);
        data[currentPage].splice(idx,1);renderSection();updateDashboardRecords();
        showToast(apiResources[currentPage]?"Record deleted.":"Demo record deleted for this session.");
      }catch(error){showToast(error.message);}
    }
  }
});
$("#tableSearch").addEventListener("input",renderSection);
$("#addRecordBtn").addEventListener("click",()=>openDialog());
$("#closeDialog").addEventListener("click",closeDialog);
$("#cancelDialog").addEventListener("click",closeDialog);
$("#recordForm").addEventListener("submit",async e=>{
  e.preventDefault();
  const form=new FormData(e.target);const record=Object.fromEntries(form.entries());
  const adding=editIndex===null;
  try{
    if(apiResources[currentPage]){
      const current=adding?null:data[currentPage][editIndex];
      const saved=await apiRequest(currentPage,adding?"POST":"PUT",current?.pk,record);
      if(adding)data[currentPage].push(saved);else data[currentPage][editIndex]=saved;
    }else if(adding)data[currentPage].push(record);else data[currentPage][editIndex]=record;
    closeDialog();renderSection();updateDashboardRecords();
    showToast(apiResources[currentPage]?(adding?"Record added.":"Record updated."):(adding?"Demo record added for this session.":"Demo record updated for this session."));
  }catch(error){showToast(error.message);}
});
$("#menuToggle").addEventListener("click",()=>$("#sidebar").classList.toggle("open"));
$("#reportBtn").addEventListener("click",()=>{
  const rows=[["Metric","Value"],["Total Students","2450"],["Total Teachers","128"],["Active Courses","32"],["Fees Collected","₹18.6L"]];
  const csv=rows.map(r=>r.map(v=>`"${String(v).replace(/"/g,'""')}"`).join(",")).join("\n");
  const blob=new Blob([csv],{type:"text/csv;charset=utf-8;"});const url=URL.createObjectURL(blob);
  const a=document.createElement("a");a.href=url;a.download="college-dashboard-report.csv";a.click();URL.revokeObjectURL(url);
  showToast("Sample dashboard report downloaded.");
});
$("#globalSearch").addEventListener("keydown",e=>{
  if(e.key==="Enter"){const q=e.target.value.trim().toLowerCase();if(!q)return;
    const page=Object.keys(data).find(p=>data[p].some(row=>Object.values(row).some(v=>String(v).toLowerCase().includes(q))));
    if(page){navigate(page);$("#tableSearch").value=e.target.value;renderSection();}else showToast("No matching sample record found.");
  }
});
$("#attendancePeriod").addEventListener("change",e=>showToast(`Chart period changed to ${e.target.value}. Demo chart data is illustrative.`));
$("#helpBtn").addEventListener("click",()=>showToast("Choose a section from the left menu to view its records."));
$("#logoutBtn").addEventListener("click",async()=>{
  try{
    const response=await fetch("/logout/",{method:"POST",headers:{"X-CSRFToken":csrfToken()}});
    if(!response.ok)throw new Error("Could not sign out. Please try again.");
    window.location.assign("/");
  }catch(error){showToast(error.message);}
});
navigate("Dashboard");
loadBackendRecords();
