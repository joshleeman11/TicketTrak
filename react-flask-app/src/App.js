import "./App.css";
import React, { useState, useEffect } from "react";
import DatePicker from "react-multi-date-picker";
import "react-calendar/dist/Calendar.css";
import _ from "lodash";

function App() {
    const [dataframe, setDataframe] = useState([]);
    const [filteredDataframe, setFilteredDataframe] = useState([]);
    const [filters, setFilters] = useState({
        minPrice: "",
        maxPrice: "",
        quantity: "",
        dates: [],
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSearch = (event) => {
        event.preventDefault();
        const updatedFilters = handleDates();
        console.log(updatedFilters.dates);
        setLoading(true);
        fetch("/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(updatedFilters),
        })
            .then((res) => {
                if (!res.ok) {
                    throw new Error("Network response was not ok");
                }
                console.log(res);
                return res.json();
            })
            .then((data) => {
                console.log(data);
                const df = JSON.parse(data);
                setDataframe(df);
                setFilteredDataframe(df);
                setLoading(false);
            })
            .catch((error) => {
                setError(error);
                setLoading(false);
            });
    };

    const sortByColumn = (column) => {
        const sortedData = _.sortBy(dataframe, (entry) => {
            const price = parseFloat(entry[column].replace(/[^0-9.-]+/g, ""));
            return price;
        });
        setFilteredDataframe(sortedData);
    };

    const handleSortByPrice = () => {
        sortByColumn("Price");
    };

    const handleDates = () => {
        let updatedDates = [];

        const addDateRange = (startDate, endDate) => {
            let currentDate = new Date(
                startDate.year,
                startDate.month.number - 1,
                startDate.day
            );
            const end = new Date(
                endDate.year,
                endDate.month.number - 1,
                endDate.day
            );

            while (currentDate <= end) {
                updatedDates.push(
                    `${
                        currentDate.getMonth() + 1
                    }-${currentDate.getDate()}-${currentDate.getFullYear()}`
                );
                currentDate.setDate(currentDate.getDate() + 1);
            }
        };

        filters.dates.forEach((range) => {
            if (range.length === 1) {
                const date = range[0];
                updatedDates.push(
                    `${date.month.number}-${date.day}-${date.year}`
                );
            } else {
                addDateRange(range[0], range[1]);
            }
        });

        console.log(updatedDates);
        const updatedFilters = {
            ...filters,
            dates: updatedDates,
        };

        setFilters(updatedFilters); // Update the filters state for future use
        return updatedFilters; // Return the updated filters to use immediately
    };

    return (
        <div className="App">
            <header className="App-header">
                <h1>TicketTrak</h1>
                {loading && <p>Loading...</p>}
                {!loading && (
                    <div>
                        <form onSubmit={handleSearch}>
                            <DatePicker
                                onChange={(event) => {
                                    setFilters({
                                        ...filters,
                                        dates: event,
                                    });
                                }}
                                multiple={true}
                                range={true}
                            ></DatePicker>
                            <select
                                name="quantity"
                                onChange={(event) =>
                                    setFilters({
                                        ...filters,
                                        quantity: event.target.value,
                                    })
                                }
                            >
                                {[...Array(11).keys()].map((num) => (
                                    <option key={num} value={num}>
                                        {num}
                                    </option>
                                ))}
                            </select>
                            <input
                                type="text"
                                name="minPrice"
                                onChange={(event) =>
                                    setFilters({
                                        ...filters,
                                        minPrice: event.target.value,
                                    })
                                }
                                placeholder="Min Price"
                            />
                            <input
                                type="text"
                                name="maxPrice"
                                onChange={(event) =>
                                    setFilters({
                                        ...filters,
                                        maxPrice: event.target.value,
                                    })
                                }
                                placeholder="Max Price"
                            />
                            <input type="submit" value="Search" />
                        </form>

                        <button onClick={handleSortByPrice}>
                            Sort By Price
                        </button>
                    </div>
                )}
                {error && <p>Error: {error.message}</p>}
                {filteredDataframe.length > 0 && (
                    <table id="ticketsTable" border="1">
                        <thead>
                            <tr>
                                <th>Team</th>
                                <th>Game Date</th>
                                <th>Section</th>
                                <th>Row</th>
                                <th>Seats</th>
                                <th>Price</th>
                                <th>Link</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredDataframe.map((entry, index) => (
                                <tr key={index}>
                                    <td>{entry["Teams"]}</td>
                                    <td>{entry["Dates"]}</td>
                                    <td>{entry["Section"]}</td>
                                    <td>{entry["Row"]}</td>
                                    <td>{entry["Seats"]}</td>
                                    <td>{entry["Price"]}</td>
                                    <td>
                                        <a href={entry["Link"]}>Link</a>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
                {filteredDataframe.length === 0 && !loading && (
                    <p>No data available.</p>
                )}
            </header>
        </div>
    );
}

export default App;
