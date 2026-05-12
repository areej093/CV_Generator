// ==================== STATE MANAGEMENT ====================
let experiences = [];
let education = [];
let skills = [];
let projects = [];

const djangoData = document.getElementById('django-data');
const isAuthenticated = djangoData ? djangoData.dataset.isAuthenticated === 'true' : false;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    setupInputListeners();
    const urlParams = new URLSearchParams(window.location.search);
    const cvId = urlParams.get('edit');
    if (cvId) loadCVForEditing(cvId);
});

function setupInputListeners() {
    const fields = ['fullName', 'email', 'phone', 'professionalTitle', 'summary', 'linkedin'];
    fields.forEach(field => {
        const el = document.getElementById(field);
        if (el) el.addEventListener('input', updatePreview);
    });
}

// ==================== DYNAMIC FIELDS ====================

function addExperience() {
    const id = Date.now();
    experiences.push(id);
    const html = `
        <div class="dynamic-item fade-in" id="exp-${id}">
            <input type="text" class="exp-position" placeholder="Position (e.g. Lead Developer)" oninput="updatePreview()">
            <input type="text" class="exp-company" placeholder="Company Name" style="margin-top: 10px;" oninput="updatePreview()">
            <input type="text" class="exp-duration" placeholder="Duration (e.g. 2020 - Present)" style="margin-top: 10px;" oninput="updatePreview()">
            <textarea class="exp-description" placeholder="What did you achieve?" rows="3" style="margin-top: 10px;" oninput="updatePreview()"></textarea>
            <button type="button" class="remove-item-btn" onclick="removeItem('exp', ${id})">Remove</button>
        </div>
    `;
    document.getElementById('experiencesContainer').insertAdjacentHTML('beforeend', html);
    updatePreview();
}

function addEducation() {
    const id = Date.now() + 1;
    education.push(id);
    const html = `
        <div class="dynamic-item fade-in" id="edu-${id}">
            <input type="text" class="edu-degree" placeholder="Degree (e.g. B.S. Computer Science)" oninput="updatePreview()">
            <input type="text" class="edu-institution" placeholder="University Name" style="margin-top: 10px;" oninput="updatePreview()">
            <input type="text" class="edu-year" placeholder="Graduation Year" style="margin-top: 10px;" oninput="updatePreview()">
            <button type="button" class="remove-item-btn" onclick="removeItem('edu', ${id})">Remove</button>
        </div>
    `;
    document.getElementById('educationContainer').insertAdjacentHTML('beforeend', html);
    updatePreview();
}

function addSkill() {
    const id = Date.now() + 2;
    skills.push(id);
    const html = `
        <div class="dynamic-item fade-in" id="skill-${id}" style="display: flex; gap: 10px; align-items: center;">
            <input type="text" class="skill-name" placeholder="Skill (e.g. Python)" oninput="updatePreview()">
            <select class="skill-level" onchange="updatePreview()">
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
                <option value="Expert">Expert</option>
            </select>
            <button type="button" class="remove-item-btn" style="margin: 0;" onclick="removeItem('skill', ${id})">×</button>
        </div>
    `;
    document.getElementById('skillsContainer').insertAdjacentHTML('beforeend', html);
    updatePreview();
}

function addProject() {
    const id = Date.now() + 3;
    projects.push(id);
    const html = `
        <div class="dynamic-item fade-in" id="project-${id}">
            <input type="text" class="project-title" placeholder="Project Name" oninput="updatePreview()">
            <textarea class="project-description" placeholder="Short description of the project..." rows="2" style="margin-top: 10px;" oninput="updatePreview()"></textarea>
            <input type="url" class="project-link" placeholder="Link (GitHub, Behance, etc.)" style="margin-top: 10px;" oninput="updatePreview()">
            <button type="button" class="remove-item-btn" onclick="removeItem('project', ${id})">Remove Project</button>
        </div>
    `;
    document.getElementById('projectsContainer').insertAdjacentHTML('beforeend', html);
    updatePreview();
}

function removeItem(type, id) {
    document.getElementById(`${type}-${id}`).remove();
    if (type === 'exp') experiences = experiences.filter(i => i !== id);
    if (type === 'edu') education = education.filter(i => i !== id);
    if (type === 'skill') skills = skills.filter(i => i !== id);
    if (type === 'project') projects = projects.filter(i => i !== id);
    updatePreview();
}

// ==================== LIVE PREVIEW ====================

function updatePreview() {
    const name = document.getElementById('fullName').value || 'Your Name';
    const title = document.getElementById('professionalTitle').value || 'Professional Title';
    const email = document.getElementById('email').value || 'email@example.com';
    const summary = document.getElementById('summary').value || 'Your professional story starts here...';
    
    // Collect projects
    const projList = [];
    document.querySelectorAll('[id^="project-"]').forEach(item => {
        const pTitle = item.querySelector('.project-title').value;
        if (pTitle) projList.push(pTitle);
    });

    const previewHtml = `
        <div style="font-family: 'Inter', sans-serif; height: 100%;">
            <div style="background: linear-gradient(135deg, #6366f1, #a855f7); padding: 40px; color: white;">
                <h1 style="margin: 0; color: white; font-size: 32px;">${name}</h1>
                <p style="opacity: 0.9; font-size: 18px;">${title}</p>
            </div>
            <div style="padding: 40px;">
                <div style="color: #6366f1; font-weight: 800; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;">Summary</div>
                <p style="color: #475569; margin-bottom: 30px;">${summary}</p>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                    <div>
                        <div style="color: #6366f1; font-weight: 800; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px;">Experience</div>
                        <div style="font-size: 14px; color: #64748b;">(Content from form appearing here...)</div>
                    </div>
                    <div>
                        <div style="color: #6366f1; font-weight: 800; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px;">Portfolio Highlights</div>
                        ${projList.map(p => `<div style="background: #f1f5f9; padding: 10px; border-radius: 10px; margin-bottom: 8px; font-weight: 700; font-size: 13px;">🚀 ${p}</div>`).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
    document.getElementById('livePreview').innerHTML = previewHtml;
}

// ==================== SAVE LOGIC ====================

async function saveCV() {
    if (!isAuthenticated) {
        alert("Please login first!");
        window.location.href = "/accounts/login/";
        return;
    }

    const cvData = {
        personalInfo: {
            name: document.getElementById('fullName').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            title: document.getElementById('professionalTitle').value,
            summary: document.getElementById('summary').value,
            linkedin: document.getElementById('linkedin').value
        },
        template: 'modern',
        experiences: [],
        education: [],
        skills: [],
        projects: []
    };

    // Collect Dynamic Data
    document.querySelectorAll('[id^="exp-"]').forEach(item => {
        cvData.experiences.push({
            position: item.querySelector('.exp-position').value,
            company: item.querySelector('.exp-company').value,
            duration: item.querySelector('.exp-duration').value,
            description: item.querySelector('.exp-description').value
        });
    });

    document.querySelectorAll('[id^="project-"]').forEach(item => {
        cvData.projects.push({
            title: item.querySelector('.project-title').value,
            description: item.querySelector('.project-description').value,
            link: item.querySelector('.project-link').value
        });
    });
    
    // Skill & Edu collection... (same pattern)
    document.querySelectorAll('[id^="skill-"]').forEach(item => {
        cvData.skills.push({
            name: item.querySelector('.skill-name').value,
            level: item.querySelector('.skill-level').value
        });
    });

    document.querySelectorAll('[id^="edu-"]').forEach(item => {
        cvData.education.push({
            degree: item.querySelector('.edu-degree').value,
            institution: item.querySelector('.edu-institution').value,
            year: item.querySelector('.edu-year').value
        });
    });

    const csrftoken = getCookie('csrftoken');
    const urlParams = new URLSearchParams(window.location.search);
    const editId = urlParams.get('edit');
    
    const url = editId ? `/api/update-cv/${editId}/` : '/api/create-cv/';
    const method = editId ? 'PUT' : 'POST';

    const response = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify(cvData)
    });

    if (response.ok) {
        alert("Success! Your professional identity is saved.");
        window.location.href = "/dashboard/";
    }
}

// ==================== UTILS ====================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Global Exports
window.addExperience = addExperience;
window.addEducation = addEducation;
window.addSkill = addSkill;
window.addProject = addProject;
window.removeItem = removeItem;
window.saveCV = saveCV;
window.updatePreview = updatePreview;
