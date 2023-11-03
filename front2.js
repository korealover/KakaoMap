const get_url = "http://127.0.0.1:5000/";

const urlInput = document.getElementById('url-input');
const submitButton = document.getElementById('submit-button');

// Enter 키를 누를 때 또는 제출 버튼을 클릭했을 때 실행할 함수
function handleSubmit() {
    console.log('init');
    const url = urlInput.value;
    console.log(url);
    //  alert('입력된 값: ' + url);

    const resultContainer = document.getElementById("average-rating");
    
      fetch(get_url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      })
        .then((response) => {
            console.log(response);
            if (response.ok) {
            console.log("response ok");
            return response.json();
            } else {
            console.log("response not ok");
            throw new Error("서버 오류");
            }
        })
        .then(data => {
        // 데이터 처리

        const reviews = data[0]; // 리뷰 데이터
        const averageStar = data[1]; // 평균 별점

        // 결과 표시
        resultContainer.innerHTML = `
            <p>${averageStar}</p>
          `;

        const posSumContainer=document.getElementById("pos-sum");
        const negSumContainer=document.getElementById("neg-sum");

        // 리뷰 리스트 생성 및 표시
        let index=0;
        for (const reviewGroup of reviews) {
            for (const review of reviewGroup) {
                const reviewText = review.summary_text;
                if(index==0){
                    posSumContainer.textContent=reviewText;
                    index++;
                }
                else if(index==1){
                    negSumContainer.textContent=reviewText;
                }
            }
        }
        })
        .catch(error => {
          console.error("Error:", error);
        });
}

// Enter 키를 눌렀을 때 실행할 이벤트 핸들러
urlInput.addEventListener('keyup', function (event) {
    if (event.key === 'Enter') {
        handleSubmit();
    }
});

// 제출 버튼을 클릭했을 때 실행할 이벤트 핸들러
submitButton.addEventListener('click', handleSubmit);