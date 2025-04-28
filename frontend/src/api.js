const API_BASE_URL = 'http://localhost:5000';

export const improveCode = async (repo_path, prompt) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chatv1`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        repo_path,
        prompt,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to improve code');
    }

    return await response.json();
  } catch (error) {
    console.error('API error:', error);
    throw error;
  }
};

