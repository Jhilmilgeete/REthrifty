// Sample products data
const products = [
    {
        id: 1,
        name: "Product 1",
        category: "Books",
        location: "Mumbai",
        price: 500,
        image: "product1.jpg"
    },
    {
        id: 2,
        name: "Product 2",
        category: "Clothes",
        location: "Delhi",
        price: 1200,
        image: "product2.jpg"
    },
    {
        id: 3,
        name: "Product 3",
        category: "Electronics",
        location: "Bangalore",
        price: 1500,
        image: "product3.jpg"
    },
    {
        id: 4,
        name: "Product 4",
        category: "Furniture",
        location: "Chennai",
        price: 800,
        image: "product4.jpg"
    }
];

// Function to display products
function displayProducts(filteredProducts) {
    const productContainer = document.querySelector('.product-listings');
    productContainer.innerHTML = ''; // Clear previous products

    filteredProducts.forEach(product => {
        const productElement = document.createElement('div');
        productElement.classList.add('product');
        productElement.innerHTML = `
            <img src="${product.image}" alt="${product.name}">
            <div class="product-info">
                <h3>${product.name}</h3>
                <p>Category: ${product.category}</p>
                <p>Location: ${product.location}</p>
                <p>Price: ₹${product.price}</p>
                <button class="view-details">View Details</button>
            </div>
        `;
        productContainer.appendChild(productElement);
    });
}

// Function to filter products based on search and filters
function filterProducts() {
    const searchTerm = document.getElementById('search').value.toLowerCase();
    const selectedCategory = document.getElementById('category').value;
    const selectedLocation = document.getElementById('location').value;
    const minPrice = document.getElementById('min-price').value;
    const maxPrice = document.getElementById('max-price').value;

    const filteredProducts = products.filter(product => {
        let matchesSearch = product.name.toLowerCase().includes(searchTerm);
        let matchesCategory = selectedCategory ? product.category === selectedCategory : true;
        let matchesLocation = selectedLocation ? product.location === selectedLocation : true;
        let matchesPrice = true;
        
        if (minPrice || maxPrice) {
            const productPrice = product.price;
            const min = minPrice ? parseInt(minPrice) : 0;
            const max = maxPrice ? parseInt(maxPrice) : Infinity;
            matchesPrice = productPrice >= min && productPrice <= max;
        }
        
        return matchesSearch && matchesCategory && matchesLocation && matchesPrice;
    });

    displayProducts(filteredProducts);
}

// Event listeners for the filter inputs
document.getElementById('search').addEventListener('input', filterProducts);
document.getElementById('category').addEventListener('change', filterProducts);
document.getElementById('location').addEventListener('change', filterProducts);
document.getElementById('min-price').addEventListener('input', filterProducts);
document.getElementById('max-price').addEventListener('input', filterProducts);

// Initialize the product display
displayProducts(products);
