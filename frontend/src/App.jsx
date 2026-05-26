import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";

function App() {
  if (window.location.pathname !== "/") {
    return <NotFoundPage />;
  }
  return <HomePage />;
}

export default App;
