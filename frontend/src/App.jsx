import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import InterviewForm from './components/InterviewForm';
import Interview from './components/Interview';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" exact element={<InterviewForm />} />
        <Route path="/interview" element={<Interview />} />
      </Routes> 
    </Router>
  );
}

export default App;
