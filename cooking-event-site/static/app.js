const form = document.querySelector(".registration-form");

if (form) {
    const countryDishes = JSON.parse(form.dataset.countryDishes);
    const countryField = document.getElementById("country");
    const dishField = document.getElementById("dish");
    const dishList = document.getElementById("dish-list");
    const memberList = document.getElementById("member-list");
    const boardTitle = document.getElementById("board-title");

    const setDishOptions = (country) => {
        const dishes = countryDishes[country] || [];
        dishField.innerHTML = "";

        if (!country) {
            dishField.disabled = true;
            dishField.innerHTML = '<option value="">Select a country first</option>';
            return;
        }

        dishField.disabled = false;
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Choose your dish";
        dishField.appendChild(placeholder);

        dishes.forEach((dish) => {
            const option = document.createElement("option");
            option.value = dish;
            option.textContent = dish;
            dishField.appendChild(option);
        });
    };

    const renderDishList = (country) => {
        const dishes = countryDishes[country] || [];
        dishList.innerHTML = "";

        if (!country) {
            dishList.classList.add("empty-state");
            dishList.innerHTML = "<li>Select a country to reveal its dish shortlist.</li>";
            return;
        }

        dishList.classList.remove("empty-state");
        dishes.forEach((dish) => {
            const item = document.createElement("li");
            item.textContent = dish;
            dishList.appendChild(item);
        });
    };

    const renderMembers = async (country) => {
        memberList.innerHTML = "";

        if (!country) {
            memberList.classList.add("empty-state");
            memberList.innerHTML = "<li>No country selected yet.</li>";
            return;
        }

        let response;
        try {
            response = await fetch(`/api/countries/${encodeURIComponent(country)}/members`);
        } catch (_error) {
            memberList.classList.add("empty-state");
            memberList.innerHTML = "<li>Unable to load teammates right now.</li>";
            return;
        }
        if (!response.ok) {
            memberList.classList.add("empty-state");
            memberList.innerHTML = "<li>Unable to load teammates right now.</li>";
            return;
        }

        const data = await response.json();
        boardTitle.textContent = `${country} team board`;

        if (!data.members.length) {
            memberList.classList.add("empty-state");
            memberList.innerHTML = "<li>No one has joined this country yet.</li>";
            return;
        }

        memberList.classList.remove("empty-state");
        data.members.forEach((member) => {
            const item = document.createElement("li");
            const name = document.createElement("strong");
            name.textContent = member.name;

            const lineBreak = document.createElement("br");

            const dish = document.createElement("span");
            dish.textContent = member.dish;

            item.appendChild(name);
            item.appendChild(lineBreak);
            item.appendChild(dish);
            memberList.appendChild(item);
        });
    };

    countryField.addEventListener("change", async (event) => {
        const country = event.target.value;
        boardTitle.textContent = country ? `${country} team board` : "Choose a country to see dishes and teammates";
        setDishOptions(country);
        renderDishList(country);
        await renderMembers(country);
    });
}
