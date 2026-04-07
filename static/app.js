function signup() {
    let users = JSON.parse(localStorage.getItem("users")) || [];

    users.push({
        email: document.getElementById("email").value,
        password: document.getElementById("password").value
    });

    localStorage.setItem("users", JSON.stringify(users));

    alert("Signup done");
}