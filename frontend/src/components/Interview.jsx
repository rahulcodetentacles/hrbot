import React, { useEffect, useState } from 'react';

const Interview = () => {
  const [question, setQuestion] = useState('');
  const [assessment, setAssessment] = useState('');
  const [interviewStarted, setInterviewStarted] = useState(false);

  const getQuestion = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/get_question');
      const data = await response.json();

      if (data.question) {
        setQuestion(data.question);
        setAssessment(''); // Clear any previous assessment
      } else {
        // All questions answered, update state to show assessment
        setAssessment(data.assessment);

        // Optional: Reset the question to an empty string to avoid confusion
        setQuestion('');
      }
    } catch (error) {
      console.error('Error getting question:', error);
    }
  };

  const getAssessment = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/get_assessment');
      const data = await response.json();

      setAssessment(data.assessment);
    } catch (error) {
      console.error('Error getting assessment:', error);
    }
  };

  const handleStartInterview = () => {
    setInterviewStarted(true);
    getQuestion();
  };

  const handleAnswerSubmission = async () => {
    try {
      // Simulate audio recording logic (replace with actual implementation)
      const audioData = 'mockAudioData';
      const response = await fetch('http://127.0.0.1:5000/submit_answer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ audio_data: audioData }),
      });
  
      // Handle the response as needed
      const data = await response.json();
      console.log(data);
  
      if (data.lastQuestion) {
        console.log('Last question received. Requesting assessment.');
        // All questions answered, get the assessment
        getAssessment();
      } else {
        console.log('Requesting the next question.');
        // More questions available, get the next question
        getQuestion();
      }
    } catch (error) {
      console.error('Error submitting audio:', error);
    }
  };  

  return (
    <div className="container d-flex flex-column align-items-center justify-content-center mt-5">
      <h1 className="text-center mb-4">HR Interview</h1>

      {!interviewStarted && (
        <button className="btn btn-primary mb-4" onClick={handleStartInterview}>
          Start Interview
        </button>
      )}

      <div
        id="question-container"
        className={`card text-center p-4 ${interviewStarted ? 'visible' : 'hidden'}`}
      >
        <p id="question" className="mb-3">
          {question}
        </p>
        <div className="mb-3">
          <audio id="audio-preview" controls style={{ display: 'none' }}></audio>
        </div>
        <button
          id="submit-answer"
          className="btn btn-primary"
          onClick={handleAnswerSubmission}
          disabled={!interviewStarted}
        >
          <i className="fas fa-microphone-alt"></i> Submit Answer
        </button>
      </div>

      <div
        id="assessment-container"
        className="card text-center p-4"
        style={{ display: assessment ? 'block' : 'none' }}
      >
        <h2 className="mb-3">Assessment Result:</h2>
        <p id="assessment">{assessment}</p>
      </div>
    </div>
  );
};

export default Interview;
