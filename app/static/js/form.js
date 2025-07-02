// form.js

function showLogin() {
    window.location.href = '/auth/login';
    clearMessages();
}

function showSignup() {
    window.location.href = '/auth/signup';
    clearMessages();
}

function goHome() {
    window.location.href = '../';
}

function clearMessages() {
    document.querySelectorAll('.error-message, .success-message').forEach(msg => {
        msg.style.display = 'none';
        msg.textContent = '';
    });
}

function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

function showSuccess(elementId, message) {
    const successElement = document.getElementById(elementId);
    if (successElement) {
        successElement.textContent = message;
        successElement.style.display = 'block';
    }
}

function handleLogin(event) {
    event.preventDefault();
    clearMessages();

    const formData = new FormData(event.target);
    const loginData = {
        emailOrUsername: formData.get('loginEmail'),
        password: formData.get('loginPassword')
    };

    // Basic validation
    if (!loginData.emailOrUsername || !loginData.password) {
        showError('loginError', 'Please fill in all fields');
        return;
    }

    if (loginData.emailOrUsername.trim().length === 0 || loginData.password.trim().length === 0) {
        showError('loginError', 'Please fill in all fields');
        return;
    }

    console.log('Login Data:', loginData);

    // Simulate API call
    setTimeout(() => {
        showSuccess('loginSuccess', 'Login successful! Redirecting...');
        setTimeout(() => {
            alert('Redirecting to dashboard...');
            // window.location.href = 'dashboard.html';
        }, 1500);
    }, 1000);
}

function handleSignup(event) {
    event.preventDefault();
    clearMessages();

    const formData = new FormData(event.target);
    const signupData = {
        firstName: formData.get('firstName'),
        lastName: formData.get('lastName'),
        username: formData.get('username'),
        email: formData.get('email'),
        phoneNumber: formData.get('phoneNumber'),
        gender: formData.get('gender'),
        password: formData.get('password'),
        confirmPassword: formData.get('confirmPassword')
    };

    // Check if all fields are filled
    if (Object.values(signupData).some(value => !value || value.trim().length === 0)) {
        showError('signupError', 'Please fill in all fields');
        return;
    }

    // Password match validation
    if (signupData.password !== signupData.confirmPassword) {
        showError('signupError', 'Passwords do not match');
        return;
    }

    // Password length validation (fixed: changed from 6 to 8 characters)
    if (signupData.password.length < 8) {
        showError('signupError', 'Password must be at least 8 characters long');
        return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(signupData.email)) {
        showError('signupError', 'Please enter a valid email address');
        return;
    }

    // Phone number validation
    const phoneRegex = /^[\d\s\-\+\(\)]{10,15}$/;
    if (!phoneRegex.test(signupData.phoneNumber)) {
        showError('signupError', 'Please enter a valid phone number (10-15 digits)');
        return;
    }

    // Username validation (additional check)
    if (signupData.username.length < 3) {
        showError('signupError', 'Username must be at least 3 characters long');
        return;
    }

    // Remove confirmPassword before sending to server
    delete signupData.confirmPassword;

    console.log('Signup Data:', signupData);

    // Simulate API call
    setTimeout(() => {
        showSuccess('signupSuccess', 'Account created successfully! Please check your email for verification.');
        setTimeout(() => {
            const form = document.getElementById('signupFormElement');
            if (form) {
                form.reset();
            }
            showLogin();
        }, 2000);
    }, 1000);
}

// DOM content loaded logic
document.addEventListener('DOMContentLoaded', function () {
    // Background shape animation
    const shapes = document.querySelectorAll('.shape');
    
    if (shapes.length > 0) {
        document.addEventListener('mousemove', function (e) {
            const mouseX = e.clientX / window.innerWidth;
            const mouseY = e.clientY / window.innerHeight;

            shapes.forEach((shape, index) => {
                const speed = (index + 1) * 0.5;
                const x = (mouseX - 0.5) * speed * 50;
                const y = (mouseY - 0.5) * speed * 50;
                shape.style.transform = `translate(${x}px, ${y}px)`;
            });
        });
    }

    // URL parameter check (only for pages that support it)
    const urlParams = new URLSearchParams(window.location.search);
    const action = urlParams.get('action');
    
    // This functionality is mainly for the main auth page if you have one
    if (action === 'signup' && typeof showSignup === 'function') {
        showSignup();
    } else if (typeof showLogin === 'function') {
        // Only call showLogin if we're not already on a specific page
        const currentPath = window.location.pathname;
        if (!currentPath.includes('/auth/login') && !currentPath.includes('/auth/signup')) {
            showLogin();
        }

    }
});