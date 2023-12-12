import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const InterviewForm = () => {
  const [yearsOfExperience, setYearsOfExperience] = useState('');
  const [position, setPosition] = useState('');

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch('http://127.0.0.1:5000/submit_form', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ years_of_experience: yearsOfExperience, position }),
      });

      // Handle the response as needed
      const data = await response.json();
      console.log(data);

      // Navigate to HR Interview page
      navigate('/interview');
    } catch (error) {
      console.error('Error submitting form:', error);
    }
  };

  return (
    <div className="container-fluid d-flex align-items-center justify-content-center vh-100">
      <div className="card p-4 text-center">
        <h1 className="mb-4">Interview Form</h1>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="years_of_experience">Years of Experience:</label>
            <input
              type="text"
              className="form-control"
              id="years_of_experience"
              name="years_of_experience"
              value={yearsOfExperience}
              onChange={(e) => setYearsOfExperience(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="position">Position:</label>
            <input
              type="text"
              className="form-control"
              id="position"
              name="position"
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              required
            />
          </div>

          <div>
            <button type="submit" className="btn btn-primary">
              Submit
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InterviewForm;
